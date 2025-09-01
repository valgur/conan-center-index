import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplFftConan(ConanFile):
    name = "nvpl_rand"
    description = "NVPL RAND library provides a collection of efficient pseudorandom and quasirandom number generators for ARM CPUs."
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "random", "rng")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

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
        self.cuda.download_package("nvpl_rand", platform_id="linux-sbsa")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_rand")

        self.cpp_info.components["nvpl_rand_"].set_property("cmake_target_name", "nvpl_rand")
        self.cpp_info.components["nvpl_rand_"].set_property("cmake_target_aliases", ["nvpl::rand", "nvpl::rand_shared"])
        self.cpp_info.components["nvpl_rand_"].libs = ["nvpl_rand"]

        self.cpp_info.components["nvpl_rand_mt"].set_property("cmake_target_name", "nvpl_rand_mt")
        self.cpp_info.components["nvpl_rand_mt"].set_property("cmake_target_aliases", ["nvpl::rand_mt", "nvpl::rand_mt_shared"])
        self.cpp_info.components["nvpl_rand_mt"].libs = ["nvpl_rand_mt"]
