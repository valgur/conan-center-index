import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaGdbConan(ConanFile):
    name = "cuda-gdb"
    description = (
        "CUDA-GDB is the NVIDIA tool for debugging CUDA applications running on Linux. "
        "CUDA-GDB is an extension to the x86-64 port of GDB, the GNU Project debugger."
    )
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cuda-gdb/"
    topics = ("cuda", "gdb", "debugger")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "python_version": ["all", "3.8", "3.9", "3.10", "3.11", "3.12"],
    }
    default_options = {
        "python_version": "all",
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def validate(self):
        self.cuda.validate_package("cuda_gdb")

    def build(self):
        self.cuda.download_package("cuda_gdb")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"), excludes="*cuda-gdb-python*")
        python_version = self.options.python_version
        if python_version == "all":
            python_version = "*"
        copy(self, f"cuda-gdb-python{python_version}-tui", self.source_folder, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = []
