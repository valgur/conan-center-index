import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudlaConan(ConanFile):
    name = "cudla"
    description = "NVIDIA Tegra Deep Learning Accelerator library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://developer.nvidia.com/cudla"
    topics = ("cuda", "tegra", "deep-learning", "deep-learning-accelerator")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "use_stubs": [True, False],
    }
    default_options = {
        "use_stubs": False,
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
        self.cuda.validate_package("libcudla")
        # libstdc++11 requirement applies to just the C++ API, so skipping the check
        # if self.settings.compiler.libcxx != "libstdc++11":
        #     raise ConanInvalidConfiguration("cudla requires libstdc++11")

    def build(self):
        self.cuda.download_package("libcudla")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::cudla")
        self.cpp_info.set_property("pkg_config_name", f"libcudla-{self.cuda.version}")
        self.cpp_info.libs = ["cudla"]
        if self.options.use_stubs:
            self.cpp_info.libdirs = ["lib/stubs", "lib"]
