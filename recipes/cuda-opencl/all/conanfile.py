import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaOpenCLConan(ConanFile):
    name = "cuda-opencl"
    description = "NVIDIA Open Computing Language (OpenCL) ICD loader library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://developer.nvidia.com/opencl"
    topics = ("cuda", "nvidia", "opencl", "icd-loader")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    provides = ["opencl-icd-loader", "opencl-headers"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            self.package_type = "static-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    @property
    def _package_name(self):
        return "cuda_opencl" if self.cuda.major >= 12 else "cuda_cudart"

    def validate(self):
        self.cuda.validate_package(self._package_name)

    def build(self):
        self.cuda.download_package(self._package_name)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include", "CL"), os.path.join(self.package_folder, "include", "CL"))
        if self.settings.os == "Linux":
            copy(self, "libOpenCL.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "OpenCL.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_target_name", "CUDA::OpenCL")
        self.cpp_info.set_property("cmake_module_file_name", "OpenCL")
        self.cpp_info.set_property("cmake_module_target_name", "OpenCL::OpenCL")
        self.cpp_info.set_property("pkg_config_name", f"opencl-{self.cuda.version}")
        self.cpp_info.libs = ["OpenCL"]
        self.cpp_info.bindirs = []
