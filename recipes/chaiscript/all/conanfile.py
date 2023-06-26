# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get, rmdir

required_conan_version = ">=1.52.0"


class ChaiScriptConan(ConanFile):
    name = "chaiscript"
    description = "Embedded Scripting Language Designed for C++."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ChaiScript/ChaiScript"
    topics = ("embedded-scripting-language", "language", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "dyn_load": [True, False],
        "use_std_make_shared": [True, False],
        "multithread_support": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "fPIC": True,
        "dyn_load": True,
        "use_std_make_shared": True,
        "multithread_support": True,
        "header_only": True,
    }
    no_copy_source = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        if self.options.header_only:
            self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_SAMPLES"] = False
        tc.variables["BUILD_MODULES"] = True
        tc.variables["USE_STD_MAKE_SHARED"] = self.options.use_std_make_shared
        tc.variables["DYNLOAD_ENABLED"] = self.options.dyn_load
        tc.variables["MULTITHREAD_SUPPORT_ENABLED"] = self.options.multithread_support
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self.options.header_only:
            copy(
                self,
                pattern="*.hpp",
                dst=os.path.join(self.package_folder, "include"),
                src=os.path.join(self.source_folder, "include"),
            )
        else:
            cmake = CMake(self)
            cmake.install()
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if not self.options.header_only:
            self.cpp_info.libs = collect_libs(self)
        if self.options.use_std_make_shared:
            self.cpp_info.defines.append("CHAISCRIPT_USE_STD_MAKE_SHARED")
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
            if self.options.multithread_support:
                self.cpp_info.system_libs.append("pthread")
