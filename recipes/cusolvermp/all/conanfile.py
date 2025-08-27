import os

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
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cusolvermp/"
    topics = ("cuda", "linear-algebra", "solver", "matrix", "decomposition", "lapack", "distributed-computing", "hpc")
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
        self.info.cuda_version = self.info.settings.cuda.version
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        cuda_major = Version(self.settings.cuda.version).major
        self._utils.cuda_requires(self, "cusolver", transitive_headers=True, transitive_libs=True)
        self._utils.cuda_requires(self, "cusparse", transitive_headers=True, transitive_libs=True)
        if cuda_major >= 12:
            self.requires(f"nvjitlink/[~{self.settings.cuda.version}]")
        if Version(self.version) >= "0.7":
            self.requires("nccl/[^2]", transitive_headers=True)
        elif cuda_major == 12:
            self.requires("cuda-cal/[>=0.4 <1]", transitive_headers=True)
        elif cuda_major == 11:
            self.requires("cuda-cal/0.4.3.36", transitive_headers=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuSOLVERMp is only supported on Linux")
        self._utils.validate_cuda_package(self, "libcusolvermp")
        self._utils.require_shared_deps(self, ["cusolver", "cusparse", "nccl", "nvjitlink"])

    def build(self):
        self._utils.download_cuda_package(self, "libcusolvermp")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["cusolverMp"]
