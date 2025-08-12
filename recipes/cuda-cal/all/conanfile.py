import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaCalConan(ConanFile):
    name = "cuda-cal"
    description = ("Communication Abstraction Library (CAL) is a helper module for the cuSOLVERMp library"
                   " that allows it to efficiently perform communications between different GPUs.")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cusolvermp/usage/cal.html"
    topics = ("cuda", "multi-gpu", "communication", "hpc")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("ucc/[^1]", options={"cuda": True})

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("CAL is only supported on Linux")
        self._utils.validate_cuda_package(self, "libcal")

    def build(self):
        self._utils.download_cuda_package(self, "libcal")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["cal"]
        self.cpp_info.requires = [
            "cudart::cudart_",
            "ucc::ucc_",
        ]
