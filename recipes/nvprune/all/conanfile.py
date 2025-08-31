import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvpruneConan(ConanFile):
    name = "nvprune"
    description = "Prunes host object files and libraries to only contain device code"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cuda-binary-utilities/"
    topics = ("cuda", "utilities", "cubin", "ptx")
    package_type = "application"
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
        self._utils.validate_cuda_package(self, "cuda_nvprune")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_nvprune")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = []
