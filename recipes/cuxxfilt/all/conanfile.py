import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuxxfiltConan(ConanFile):
    name = "cuxxfilt"
    description = "cu++filt decodes (demangles) low-level identifiers that have been mangled by CUDA C++ into user-readable names."
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cuda-binary-utilities/"
    topics = ("cuda", "utilities", "demangler")
    package_type = "static-library"
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

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_cuxxfilt")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cuxxfilt")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib", "x64") if self.settings.os == "Windows" else os.path.join(self.source_folder, "lib")
        copy(self, "*", libdir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["cufilt"]
        self.cpp_info.system_libs = ["gcc_s", "stdc++"]
