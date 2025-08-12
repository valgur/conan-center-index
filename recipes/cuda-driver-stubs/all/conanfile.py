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
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        copy(self, "CUDAToolkit-wrapper.cmake", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_cudart")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cudart")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "cuda.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            copy(self, "libcuda.so", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cuda.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        copy(self, "CUDAToolkit-wrapper.cmake", self.export_sources_folder, os.path.join(self.package_folder, "share", "conan"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::cuda_driver")
        v = Version(self.version)
        self.cpp_info.set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        self.cpp_info.libs = ["cuda"]

        # Also install the wrapper for FindCUDAToolkit.cmake as cuda-driver-stubs is the root dependency for all other CUDA toolkit packages
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "CUDAToolkit")
        self.cpp_info.set_property("cmake_build_modules", ["share/conan/CUDAToolkit-wrapper.cmake"])
        self.cpp_info.builddirs = ["share/conan"]
