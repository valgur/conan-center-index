import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuPqcConan(ConanFile):
    name = "cupqc"
    description = ("NVIDIA cuPQC is an SDK of optimized libraries for implementing"
                   " GPU-accelerated Post-Quantum Cryptography (PQC) workflows")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Math-SDK-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cupqc/"
    topics = ("cuda", "cryptography", "post-quantum", "nvidia", "gpu-acceleration")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Only Linux is supported")
        if self.settings.arch not in ["x86_64", "armv8"]:
            raise ConanInvalidConfiguration("Only x86_64 and armv8 are supported")

    def build(self):
        platform = "linux-x86_64" if self.settings.arch == "x86_64" else "linux-aarch64"
        get(self, **self.conan_data["sources"][self.version][platform], strip_root=True, destination=self.source_folder)

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.cuh", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # Also installs a cuhash-config.cmake officially
        self.cpp_info.set_property("cmake_file_name", "cupqc")

        self.cpp_info.components["cuhash"].set_property("cmake_target_name", "cuhash")
        self.cpp_info.components["cuhash"].set_property("cmake_target_aliases", ["cuhash_static"])
        self.cpp_info.components["cuhash"].includedirs = ["include/cupqc", "include/commondx", "include"]
        self.cpp_info.components["cuhash"].libs = ["cuhash"]

        self.cpp_info.components["cupqc"].set_property("cmake_target_name", "cupqc")
        self.cpp_info.components["cupqc"].set_property("cmake_target_aliases", ["cupqc_static"])
        self.cpp_info.components["cupqc"].includedirs = ["include/cupqc", "include/commondx", "include"]
        self.cpp_info.components["cupqc"].libs = ["cupqc"]
