import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudartConan(ConanFile):
    name = "cudart"
    description = "CUDA Runtime architecture dependent libraries"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "runtime")
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

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        del self.info.options.cmake_alias

    def requirements(self):
        v = Version(self.version)
        self.requires(f"cuda-crt/[~{v.major}.{v.minor}]", transitive_headers=True, transitive_libs=True)
        self.requires(f"cuda-driver-stubs/[~{v.major}.{v.minor}]", transitive_headers=True, transitive_libs=True)
        cccl_range = self._utils.get_version_range("cuda-cccl", self.version)
        self.requires(f"cuda-cccl/[{cccl_range}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_cudart")
        if not Version(self.version).in_range(f"~{self.settings.cuda.version}"):
            raise ConanInvalidConfiguration(f"Version {self.version} is not compatible with the cuda.version {self.settings.cuda.version} setting")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cudart")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "libcudart.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "libcudart_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            copy(self, "libcudadevrt.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            if self.options.shared:
                copy(self, "cudart.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
            else:
                copy(self, "cudart_static.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            copy(self, "cudadevrt.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        lib = "cudart" if self.options.shared else "cudart_static"
        self.cpp_info.components["cudart_"].set_property("cmake_target_name", f"CUDA::{lib}")
        v = Version(self.version)
        self.cpp_info.components["cudart_"].set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        if self.options.cmake_alias:
            alias = "cudart_static" if self.options.shared else "cudart"
            self.cpp_info.components["cudart_"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cudart_"].libs = [lib]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cudart_"].system_libs = ["pthread", "dl", "rt"]
            # cudart_static relies on two libstdc++ symbols: __cxa_atexit and __dso_handle
            # These can be provided by libc++abi for libc++.
            if self.settings.get_safe("compiler.libcxx") == "libc++":
                self.cpp_info.components["cudart_"].system_libs.append("c++abi")
            else:
                self.cpp_info.components["cudart_"].system_libs.append("stdc++")
        self.cpp_info.components["cudart_"].requires = [
            "cuda-crt::cuda-crt",
            "cuda-driver-stubs::cuda-driver-stubs",
            "cuda-cccl::cuda-cccl",
        ]

        self.cpp_info.components["cudadevrt"].set_property("cmake_target_name", "CUDA::cudadevrt")
        self.cpp_info.components["cudadevrt"].libs = ["cudadevrt"]
        self.cpp_info.components["cudadevrt"].requires = ["cudart_"]
