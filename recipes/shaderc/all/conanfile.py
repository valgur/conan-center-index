# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class ShadercConan(ConanFile):
    name = "shaderc"
    description = "A collection of tools, libraries and tests for shader compilation."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/shaderc"
    topics = ("glsl", "hlsl", "msl", "spirv", "spir-v", "glslc", "spvc")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "spvc": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "spvc": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) >= "2020.4":
            self.options.rm_safe("spvc")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _get_compatible_spirv_tools_version(self):
        return {
            "2021.1": "2021.2",
            "2019.0": "2020.5",
        }.get(str(self.version), False)

    @property
    def _get_compatible_glslang_version(self):
        return {
            "2021.1": "11.5.0",
            "2019.0": "8.13.3559",
        }.get(str(self.version), False)

    def requirements(self):
        self.requires("glslang/{}".format(self._get_compatible_glslang_version))
        self.requires("spirv-tools/{}".format(self._get_compatible_spirv_tools_version))
        if self.options.get_safe("spvc", False):
            self.requires("spirv-cross/20210115")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.variables["SHADERC_ENABLE_SPVC"] = self.options.get_safe("spvc", False)
        tc.variables["SHADERC_SKIP_INSTALL"] = False
        tc.variables["SHADERC_SKIP_TESTS"] = True
        tc.variables["SHADERC_SPVC_ENABLE_DIRECT_LOGGING"] = False
        tc.variables["SHADERC_SPVC_DISABLE_CONTEXT_LOGGING"] = False
        tc.variables["SHADERC_ENABLE_WERROR_COMPILE"] = False
        if self.settings.compiler == "Visual Studio":
            tc.variables["SHADERC_ENABLE_SHARED_CRT"] = str(self.settings.compiler.runtime).startswith("MD")
        tc.variables["ENABLE_CODE_COVERAGE"] = False
        if is_apple_os(self.settings.os):
            tc.variables["CMAKE_MACOSX_BUNDLE"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "shaderc" if self.options.shared else "shaderc_static")
        self.cpp_info.libs = self._get_ordered_libs()
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.system_libs.append(stdcpp_library(self))
        if self.options.shared:
            self.cpp_info.defines.append("SHADERC_SHAREDLIB")

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)

    def _get_ordered_libs(self):
        libs = ["shaderc_shared" if self.options.shared else "shaderc"]
        if not self.options.shared:
            libs.append("shaderc_util")
        if self.options.get_safe("spvc", False):
            libs.append("shaderc_spvc_shared" if self.options.shared else "shaderc_spvc")
        return libs
