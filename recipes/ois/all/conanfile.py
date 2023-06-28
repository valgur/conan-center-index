# TODO: verify the Conan v2 migration

import glob
import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    copy,
    export_conandata_patches,
    get,
    rmdir,
)

required_conan_version = ">=1.53.0"


class OisConan(ConanFile):
    name = "ois"
    description = "Object oriented Input System."
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/wgois/OIS"
    topics = "input"
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
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("xorg/system")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OIS_BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["OIS_BUILD_DEMOS"] = False
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        for pdb_file in glob.glob(os.path.join(self.package_folder, "bin", "*.pdb")):
            os.unlink(pdb_file)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

        self.cpp_info.set_property("pkg_config_name", "OIS")
        self.cpp_info.names["cmake_find_package"] = "OIS"
        self.cpp_info.names["cmake_find_package_multi"] = "OIS"

        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["Foundation", "Cocoa", "IOKit"]
        elif self.settings.os == "Windows":
            self.cpp_info.defines = ["OIS_WIN32_XINPUT_SUPPORT"]
            self.cpp_info.system_libs = ["dinput8", "dxguid"]
            if self.options.shared:
                self.cpp_info.defines.append("OIS_DYNAMIC_LIB")
