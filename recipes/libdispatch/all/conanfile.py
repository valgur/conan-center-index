# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.53.0"


class LibDispatchConan(ConanFile):
    name = "libdispatch"
    description = (
        "Grand Central Dispatch (GCD or libdispatch) provides comprehensive support "
        "for concurrent code execution on multicore hardware."
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/apple/swift-corelibs-libdispatch"
    topics = ("apple", "GCD", "concurrency")

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler != "clang":
            raise ConanInvalidConfiguration("Clang compiler is required.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "swift-corelibs-{}-swift-{}-RELEASE".format(self.name, self.version)
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        if self.settings.os == "Macos":
            self.cpp_info.libs = ["dispatch"]
        else:
            self.cpp_info.libs = ["dispatch", "BlocksRuntime"]

        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "rt"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["shlwapi", "ws2_32", "winmm", "synchronization"]
