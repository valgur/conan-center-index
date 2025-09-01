import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvmlStubsConan(ConanFile):
    name = "nvml-stubs"
    description = "NVML: NVIDIA Management Library stubs"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://developer.nvidia.com/management-library-nvml"
    topics = ("cuda", "nvidia", "management", "monitoring", "data-center", "gpu")
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

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows" or Version(self.version) < "12.4":
            del self.options.shared
            self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")

    def validate(self):
        self.cuda.validate_package("cuda_nvml_dev")

    def build(self):
        self.cuda.download_package("cuda_nvml_dev")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.get_safe("shared", True):
                copy(self, "libnvidia-ml.so", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "libnvidia-ml.a", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
        else:
            copy(self, "nvml.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        self.cpp_info.set_property("pkg_config_name", f"nvidia-ml-{self.cuda.version}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::nvml{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::nvml{alias_suffix}"])
        self.cpp_info.libs = ["nvidia-ml" if self.settings.os == "Linux" else "nvml"]
        if self.settings.os == "Linux":
            self.cpp_info.libdirs = ["lib/stubs"]
        self.cpp_info.bindirs = []
        if self.settings.os == "Linux" and not self.options.get_safe("shared", True):
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl"]
