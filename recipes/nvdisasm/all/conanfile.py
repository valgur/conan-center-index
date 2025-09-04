import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvdisasmConan(ConanFile):
    name = "nvdisasm"
    description = "nvdisasm extracts information from standalone cubin files and presents them in a human readable format"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cuda-binary-utilities/"
    topics = ("cuda", "utilities", "disassembler", "cubin", "ptx")
    package_type = "application"
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
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major

    def validate(self):
        self.cuda.validate_package("cuda_nvdisasm")

    def build(self):
        self.cuda.download_package("cuda_nvdisasm")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = []
