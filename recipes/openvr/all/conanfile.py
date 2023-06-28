# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    copy,
    export_conandata_patches,
    get,
    replace_in_file,
    rmdir,
)
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class OpenvrConan(ConanFile):
    name = "openvr"
    description = (
        "API and runtime that allows access to VR hardware from applications "
        "have specific knowledge of the hardware they are targeting."
    )
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ValveSoftware/openvr"
    topics = ("openvr", "vr")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "11")

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration(
                "OpenVR can't be compiled by {0} {1}".format(
                    self.settings.compiler, self.settings.compiler.version
                )
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("jsoncpp/1.9.4")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_UNIVERSAL"] = False
        tc.variables["USE_LIBCXX"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Honor fPIC=False
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "-fPIC", "")
        # Unvendor jsoncpp (we rely on our CMake wrapper for jsoncpp injection)
        replace_in_file(self, os.path.join(self.source_folder, "src", "CMakeLists.txt"), "jsoncpp.cpp", "")
        rmdir(self, os.path.join(self.source_folder, "src", "json"))

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            pattern="openvr_api*.dll",
            dst=os.path.join(self.package_folder, "bin"),
            src="bin",
            keep_path=False,
        )
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "openvr")
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "openvr"))

        if not self.options.shared:
            self.cpp_info.defines.append("OPENVR_BUILD_STATIC")
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("dl")

        if is_apple_os(self.settings.os):
            self.cpp_info.frameworks.append("Foundation")
