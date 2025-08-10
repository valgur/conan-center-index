import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaCrtConan(ConanFile):
    name = "cuda-crt"
    description = "CUDA Runtime internal headers"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "nvcc")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_nvcc")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_nvcc")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include", "crt"), os.path.join(self.package_folder, "include", "crt"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
