import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CusolvermpConan(ConanFile):
    name = "cusolvermp"
    description = ("NVIDIA cuSOLVERMp is a high-performance, distributed-memory, GPU-accelerated library"
                   " that provides tools for the solution of dense linear systems and eigenvalue problems.")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Math-SDK-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cusolvermp/"
    topics = ("cuda", "linear-algebra", "solver", "matrix", "decomposition", "lapack", "distributed-computing", "hpc")
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
        self.info.cuda_version = self.info.settings.cuda.version
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.cuda.requires("cusolver", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cusparse", transitive_headers=True, transitive_libs=True)
        if self.cuda.major >= 12:
            self.cuda.requires("nvjitlink")
        if Version(self.version) >= "0.7":
            self.requires("nccl/[^2]", transitive_headers=True)
        elif self.cuda.major == 12:
            self.requires("cuda-cal/[>=0.4 <1]", transitive_headers=True)
        elif self.cuda.major == 11:
            self.requires("cuda-cal/0.4.3.36", transitive_headers=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuSOLVERMp is only supported on Linux")
        self.cuda.validate_package("libcusolvermp")
        self.cuda.require_shared_deps(["cusolver", "cusparse", "nccl", "nvjitlink"])

    def build(self):
        self.cuda.download_package("libcusolvermp")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["cusolverMp"]
