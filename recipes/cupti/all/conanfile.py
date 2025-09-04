import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuptiConan(ConanFile):
    name = "cupti"
    description = "CUPTI: NVIDIA CUDA profiling tools interface library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cupti/"
    topics = ("cuda", "profiling")
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
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self.cuda.validate_package("cuda_cupti")

    def build(self):
        self.cuda.download_package("cuda_cupti")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        # cupti
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        self.cpp_info.components["cupti_"].set_property("cmake_target_name", f"CUDA::cupti{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["cupti_"].set_property("cmake_target_aliases", [f"CUDA::cupti{alias_suffix}"])
        self.cpp_info.components["cupti_"].libs = [f"cupti{suffix}"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cupti_"].system_libs = ["rt", "pthread", "m", "dl", "util", "gcc_s", "stdc++"]
        self.cpp_info.components["cupti_"].requires = ["cudart::cudart_"]

        # nvperf_host
        self.cpp_info.components["nvperf_host"].set_property("cmake_target_name", f"CUDA::nvperf_host{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["nvperf_host"].set_property("cmake_target_aliases", [f"CUDA::nvperf_host{alias_suffix}"])
        self.cpp_info.components["nvperf_host"].libs = [f"nvperf_host{suffix}"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["nvperf_host"].system_libs = ["rt", "pthread", "m", "dl", "util", "gcc_s", "stdc++"]

        if self.options.get_safe("shared", True):
            # nvperf_target
            self.cpp_info.components["nvperf_target"].set_property("cmake_target_name", "CUDA::nvperf_target")
            self.cpp_info.components["nvperf_target"].libs = ["nvperf_target"]

            # pcsamplingutil
            self.cpp_info.components["pcsamplingutil"].set_property("cmake_target_name", "CUDA::pcsamplingutil")
            self.cpp_info.components["pcsamplingutil"].libs = ["pcsamplingutil"]
            self.cpp_info.components["pcsamplingutil"].requires = ["cupti_"]

            # checkpoint
            self.cpp_info.components["checkpoint"].set_property("cmake_target_name", "CUDA::checkpoint")
            self.cpp_info.components["checkpoint"].libs = ["checkpoint"]
            self.cpp_info.components["checkpoint"].requires = ["cupti_"]
