import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CublasMpConan(ConanFile):
    name = "cublasmp"
    description = "cuBLASMp: a high-performance, multi-process, GPU-accelerated library for distributed basic dense linear algebra"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cublasmp/"
    topics = ("cuda", "blas", "linear-algebra", "distributed-computing", "hpc")
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
        self.requires(f"cublas/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("nccl/[^2.18.5]", transitive_headers=True)
        self.requires("nvshmem/[^3.1]", run=True)
        if Version(self.version) < "0.5":
            if Version(self.settings.cuda.version).major > 11:
                self.requires("cuda-cal/[>=0.4 <1]", transitive_headers=True, transitive_libs=True)
            else:
                self.requires("cuda-cal/0.4.3.36", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuBLASMp is only supported on Linux")
        self._utils.validate_cuda_package(self, "libcublasmp")

    def build(self):
        self._utils.download_cuda_package(self, "libcublasmp")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["cublasmp"]
        self.cpp_info.requires = [
            "cublas::cublas_",
            "cublas::cublasLt",
            "nvshmem::nvshmem_host",
            "nccl::nccl",
        ]
        if Version(self.version) < "0.5":
            self.cpp_info.requires.append("cuda-cal::cuda-cal")
