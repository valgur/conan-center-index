import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvFatbinConan(ConanFile):
    name = "nvfatbin"
    description = "nvFatbin: NVIDIA compiler library for fat binary (fatbin) creation"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/nvfatbin/"
    topics = ("cuda", "fatbin", "ptx", "compiler")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.use_stubs

    def configure(self):
        if not self.options.shared:
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def validate(self):
        self._utils.validate_cuda_package(self, "libnvfatbin")

    def build(self):
        self._utils.download_cuda_package(self, "libnvfatbin")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            if self.options.shared:
                copy(self, "nvfatbin*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
                copy(self, "nvfatbin.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""
        v = self._cuda_version
        self.cpp_info.set_property("pkg_config_name", f"nvfatbin-{v.major}.{v.minor}")
        self.cpp_info.set_property("system_package_version", f"{v.major}.{v.minor}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::nvfatbin{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::nvfatbin{alias_suffix}"])
        self.cpp_info.libs = [f"nvfatbin{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.libdirs = ["lib/stubs", "lib"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
