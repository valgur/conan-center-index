import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvTiffConan(ConanFile):
    name = "nvtiff"
    description = "nvTIFF is a GPU-accelerated TIFF encode/decode library built on the CUDA platform"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/nvtiff/"
    topics = ("cuda", "tiff", "codec")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.cuda_version = self.info.settings.cuda.version
        del self.info.settings.cuda
        self.info.settings.rm_safe("cmake_alias")

    @cached_property
    def _cuda_version(self):
        return self.dependencies["cudart"].ref.version

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libnvtiff")
        if self.settings.os == "Linux" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("nvtiff requires libstdc++11")

    def build(self):
        self._utils.download_cuda_package(self, "libnvtiff")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib")
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", libdir, os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dll", libdir, os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", libdir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        v = self._cuda_version
        # Neither the CMake nor .pc name is official
        self.cpp_info.set_property("pkg_config_name", f"nvtiff-{v.major}.{v.minor}")
        self.cpp_info.set_property("system_package_version", f"{v.major}.{v.minor}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::nvtiff{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::nvtiff{alias_suffix}"])
        self.cpp_info.libs = [f"nvtiff{suffix}"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
