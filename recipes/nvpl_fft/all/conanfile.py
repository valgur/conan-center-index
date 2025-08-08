import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplFftConan(ConanFile):
    name = "nvpl_fft"
    description = ("The NVIDIA Performance Libraries (NVPL) FFT library enables you to perform"
                   " Fast Fourier Transform (FFT) calculations on ARM CPUs.")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "fft", "fftw", "fast-fourier-transform")
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

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on Linux")
        if self.settings.arch != "armv8":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on armv8")

    def build(self):
        self._utils.download_cuda_package(self, "nvpl_fft", platform_id="linux-sbsa")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_fft")
        self.cpp_info.set_property("cmake_target_name", "nvpl_fftw")
        self.cpp_info.set_property("cmake_target_aliases", ["nvpl::fftw"])
        self.cpp_info.libs = ["nvpl_fftw"]
        self.cpp_info.includedirs.append("include/nvpl_fftw")
