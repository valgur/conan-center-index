import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvMatmulHeuristicsConan(ConanFile):
    name = "nvmatmulheuristics"
    description = ("NVIDIA Matmul Heuristics (nvMatmulHeuristics) is a GPU optimization module that provides fast,"
                   " analytic heuristics for GPU tensor operations, particularly matrix multiplications (GEMMs).")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Math-SDK-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/nvidia-matmul-heuristics/"
    topics = ("nvidia", "cuda", "gpu", "math", "matrix", "gemm", "heuristics")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("nvMatmulHeuristics is only supported on Linux")
        if self.settings.arch not in ["x86_64", "armv8"]:
            raise ConanInvalidConfiguration("nvMatmulHeuristics is only supported on x86_64 and armv8 architectures")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.arch)], strip_root=True, destination=self.source_folder)

    def package(self):
        copy(self, "*", os.path.join(self.source_folder, "licenses"), os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "nvMatmulHeuristics"), self.package_folder)
        # Make a symlink from libnvMatmulHeuristics.so.0
        major = Version(self.version).major
        with chdir(self, os.path.join(self.package_folder, "lib")):
            os.symlink(f"libnvMatmulHeuristics.so.{major}", "libnvMatmulHeuristics.so")

    def package_info(self):
        # The CMake names are not official
        self.cpp_info.set_property("cmake_file_name", "nvMatmulHeuristics")
        self.cpp_info.set_property("cmake_target_name", "nvMatmulHeuristics::nvMatmulHeuristics")
        self.cpp_info.libs = ["nvMatmulHeuristics"]
