import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class JitifyConan(ConanFile):
    name = "jitify"
    description = "A single-header C++ library for simplifying the use of CUDA Runtime Compilation (NVRTC)"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVIDIA/jitify"
    topics = ("cuda", "jit", "nvrtc", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        self.requires(f"nvrtc/[~{self.settings.cuda.version}]")

    def validate(self):
        self._utils.validate_cuda_settings(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "jitify.hpp", self.source_folder, os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
