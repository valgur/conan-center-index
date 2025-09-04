import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CublasMpConan(ConanFile):
    name = "cublasmp"
    description = "cuBLASMp: a high-performance, multi-process, GPU-accelerated library for distributed basic dense linear algebra"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Math-SDK-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cublasmp/"
    topics = ("cuda", "blas", "linear-algebra", "distributed-computing", "hpc")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major

    def requirements(self):
        self.cuda.requires("cublas", transitive_headers=True, transitive_libs=True)
        self.requires("nvshmem/[^3.1]", run=True)
        if Version(self.version) >= "0.5":
            self.requires("nccl/[^2.18.5]", transitive_headers=True)
        elif self.cuda.major == 12:
            self.requires("cuda-cal/[>=0.4 <1]", transitive_headers=True)
        elif self.cuda.major == 11:
            self.requires("cuda-cal/0.4.3.36", transitive_headers=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuBLASMp is only supported on Linux")
        self.cuda.validate_package("libcublasmp")
        self.cuda.require_shared_deps(["cudart", "cublas", "nvshmem", "nccl", "nvshmem"])

    def build(self):
        self.cuda.download_package("libcublasmp")

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
        ]
        if Version(self.version) >= "0.5":
            self.cpp_info.requires.append("nccl::nccl")
        else:
            self.cpp_info.requires.append("cuda-cal::cuda-cal")
