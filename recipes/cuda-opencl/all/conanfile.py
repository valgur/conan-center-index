import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudaOpenCLConan(ConanFile):
    name = "cuda-opencl"
    description = "NVIDIA Open Computing Language (OpenCL) library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/opencl"
    topics = ("cuda", "nvidia", "opencl")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    python_requires = "conan-utils/latest"

    def config_options(self):
        if self.settings.os == "Windows":
            self.package_type = "static-library"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_opencl")
        if self.settings.os == "Linux" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("cuda-opencl requires libstdc++11")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_opencl")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            copy(self, "libOpenCL.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "OpenCL.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        v = self._cuda_version
        self.cpp_info.set_property("pkg_config_name", f"opencl-{v.major}.{v.minor}")
        self.cpp_info.set_property("system_package_version", f"{v.major}.{v.minor}")
        self.cpp_info.set_property("cmake_target_name", "CUDA::OpenCL")
        self.cpp_info.libs = ["OpenCL"]
        self.cpp_info.bindirs = []
