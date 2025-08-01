import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudaDriverStubsConan(ConanFile):
    name = "cuda-driver-stubs"
    description = "Stubs for the CUDA Driver library (libcuda.so)"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "driver")
    package_type = "shared-library"
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

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cudart")

    def package(self):
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "cuda.h", os.path.join(self.build_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            copy(self, "libcuda.so", os.path.join(self.build_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cuda.lib", os.path.join(self.build_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::cuda_driver")
        v = Version(self.version)
        self.cpp_info.set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        self.cpp_info.set_property("system_package_version", f"{v.major}.{v.minor}")
        self.cpp_info.libs = ["cuda"]
