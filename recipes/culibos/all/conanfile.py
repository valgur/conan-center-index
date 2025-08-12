import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CulibosConan(ConanFile):
    name = "culibos"
    description = "CUDA internal backend thread abstraction layer library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "runtime")
    package_type = "static-library"
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

    @property
    def _package(self):
        return "cuda_culibos" if Version(self.version) >= "13.0" else "cuda_cudart"

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("culibos is only available and needed on Linux")
        self._utils.validate_cuda_package(self, self._package)

    def build(self):
        self._utils.download_cuda_package(self, self._package)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "libculibos.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::culibos")
        self.cpp_info.libs = ["culibos"]
        self.cpp_info.bindirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.system_libs = ["pthread", "dl", "rt"]
