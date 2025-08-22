import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class CnmemConan(ConanFile):
    name = "cnmem"
    description = "A simple memory manager for CUDA designed to help Deep Learning frameworks manage memory"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVIDIA/cnmem"
    topics = ("cuda", "nvidia", "memory-management", "deep-learning")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    languages = ["C"]

    def configure(self):
        del self.settings.cuda.architectures
        del self.settings.cuda.platform

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, libs=False)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 compatibility
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.8)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["cnmem"]
