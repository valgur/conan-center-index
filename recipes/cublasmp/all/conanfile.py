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
    default_options = {
        "cublas/*:shared": True,
        "nccl/*:shared": True,
        "ucc/*:shared": True,
    }

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
        cuda_major = Version(self.settings.cuda.version).major
        self.requires(f"cublas/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("nvshmem/[^3.1]", run=True)
        if Version(self.version) >= "0.5":
            self.requires("nccl/[^2.18.5]", transitive_headers=True)
        elif cuda_major == 12:
            self.requires("cuda-cal/[>=0.4 <1]", transitive_headers=True)
        elif cuda_major == 11:
            self.requires("cuda-cal/0.4.3.36", transitive_headers=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuBLASMp is only supported on Linux")
        if not self.dependencies["cudart"].options.shared:
            raise ConanInvalidConfiguration("cuBLASMp requires -o cudart/*:shared=True")
        if not self.dependencies["cublas"].options.get_safe("shared", True):
            raise ConanInvalidConfiguration("cuBLASMp requires -o cublas/*:shared=True")
        if Version(self.version) >= "0.5" and not self.dependencies["nccl"].options.shared:
            raise ConanInvalidConfiguration("cuBLASMp requires -o nccl/*:shared=True")
        if not self.dependencies["ucc"].options.get_safe("shared", True):
            raise ConanInvalidConfiguration("cuBLASMp requires -o ucc/*:shared=True")
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
        ]
        if Version(self.version) >= "0.5":
            self.cpp_info.requires.append("nccl::nccl")
        else:
            self.cpp_info.requires.append("cuda-cal::cuda-cal")
