import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudlaConan(ConanFile):
    name = "cudla"
    description = "NVIDIA Tegra Deep Learning Accelerator library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cudla"
    topics = ("cuda", "tegra", "deep-learning", "deep-learning-accelerator")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "use_stubs": [True, False],
    }
    default_options = {
        "use_stubs": True,
    }

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
        self._utils.validate_cuda_package(self, "libcudla")
        if self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("cudla requires libstdc++11")

    def build(self):
        self._utils.download_cuda_package(self, "libcudla")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        v = Version(self.version)
        self.cpp_info.set_property("cmake_target_name", "CUDA::cudla")
        self.cpp_info.set_property("pkg_config_name", f"libcudla-{v.major}.{v.minor}")
        self.cpp_info.set_property("system_package_version", f"{v.major}.{v.minor}")
        self.cpp_info.libs = ["cudla"]
        if self.options.use_stubs:
            self.cpp_info.libdirs = ["lib/stubs"]
