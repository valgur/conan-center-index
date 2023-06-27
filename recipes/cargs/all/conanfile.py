# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get

required_conan_version = ">=1.53.0"


class CargsConan(ConanFile):
    name = "cargs"
    description = (
        "A lightweight getopt replacement that works on Linux, "
        "Windows and macOS. Command line argument parser library"
        " for C/C++. Can be used to parse argv and argc parameters."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://likle.github.io/cargs/"
    topics = (
        "cargs",
        "cross-platform",
        "windows",
        "macos",
        "osx",
        "linux",
        "getopt",
        "getopt-long",
        "command-line-parser",
        "command-line",
        "arguments",
        "argument-parser",
    )

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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = (
            self.options.shared and self.settings.os == "Windows"
        )
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="cargs")

    def package(self):
        include_dir = os.path.join(self.source_folder, "include")
        lib_dir = os.path.join(self.build_folder, "lib")
        bin_dir = os.path.join(self.build_folder, "bin")

        copy(self, "LICENSE.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "cargs.h", dst=os.path.join(self.package_folder, "include"), src=include_dir)
        for pattern in ["*.a", "*.so", "*.dylib", "*.lib"]:
            copy(self, pattern, dst=os.path.join(self.package_folder, "lib"), src=lib_dir, keep_path=False)
        copy(
            self, pattern="*.dll", dst=os.path.join(self.package_folder, "bin"), src=bin_dir, keep_path=False
        )

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
