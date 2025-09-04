import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvptxcompilerLibsConan(ConanFile):
    name = "nvptxcompiler"
    description = "CUDA PTX Compiler APIs"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "ptx", "jit", "compiler")
    package_type = "static-library"
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

    @property
    def _package(self):
        return "cuda_nvcc" if Version(self.version) < "13.0" else "libnvptxcompiler"

    def validate(self):
        self.cuda.validate_package(self._package)

    def build(self):
        self.cuda.download_package(self._package)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "nvPTXCompiler.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib") if self.settings.os == "Linux" else os.path.join(self.source_folder, "lib", "x64")
        copy(self, "*", libdir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::nvptxcompiler_static")
        self.cpp_info.libs = ["nvptxcompiler_static"]
        self.cpp_info.bindirs = []
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m", "dl", "pthread", "gcc_s"]
            if self.settings.get_safe("compiler.libcxx") == "libc++":
                self.cpp_info.system_libs.append("c++abi")
            else:
                self.cpp_info.system_libs.append("stdc++")
