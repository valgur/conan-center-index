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

    def config_options(self):
        if self.options.shared:
            self.package_type = "shared-library"
        else:
            self.package_type = "static-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda
        del self.info.options.cmake_alias

    def requirements(self):
        v = Version(self.version)
        self.requires(f"nvcc-headers/[~{v.major}.{v.minor}]", transitive_headers=True)
        self.requires(f"cuda-driver-stubs/[~{v.major}.{v.minor}]", transitive_headers=True, transitive_libs=True)
        self.requires("libcudacxx/[^2]", transitive_headers=True)

    def validate(self):
        if not Version(self.version).in_range(f"~{self.settings.cuda.version}"):
            raise ConanInvalidConfiguration(f"Version {self.version} is not compatible with the cuda.version {self.settings.cuda.version} setting")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cudart")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
        if self.settings.os == "Windows":
            copy(self, "*.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            rm(self, "cuda.lib", os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "lib", "stubs"))
        if self.options.shared:
            rm(self, "*cudart_static.*", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*cudart.*", os.path.join(self.package_folder, "lib"))
            rm(self, "*cudart.*", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        # TODO: create a complete wrapper for CUDAToolkit.cmake
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "CUDAToolkit")

        lib = "cudart" if self.options.shared else "cudart_static"
        self.cpp_info.components["cudart_"].set_property("cmake_target_name", f"CUDA::{lib}")
        v = Version(self.version)
        self.cpp_info.components["cudart_"].set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        self.cpp_info.components["cudart_"].set_property("component_version", f"{v.major}.{v.minor}")
        if self.options.cmake_alias:
            alias = "cudart_static" if self.options.shared else "cudart"
            self.cpp_info.components["cudart_"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cudart_"].libs = [lib]
        if self.settings.os == "Linux":
            self.cpp_info.components["cudart_"].bindirs = []
            self.cpp_info.components["cudart_"].system_libs = ["rt", "pthread", "dl"]
        self.cpp_info.components["cudart_"].requires = [
            "nvcc-headers::nvcc-headers",
            "cuda-driver-stubs::cuda-driver-stubs",
            "libcudacxx::libcudacxx",
        ]

        self.cpp_info.components["cudadevrt"].set_property("cmake_target_name", "CUDA::cudadevrt")
        self.cpp_info.components["cudadevrt"].libs = ["cudadevrt"]
        self.cpp_info.components["cudadevrt"].requires = ["nvcc-headers::nvcc-headers", "cuda-driver-stubs::cuda-driver-stubs"]

        if self.settings.os == "Linux":
            self.cpp_info.components["culibos"].set_property("cmake_target_name", "CUDA::culibos")
            self.cpp_info.components["culibos"].libs = ["culibos"]
            self.cpp_info.components["culibos"].requires = ["nvcc-headers::nvcc-headers", "cuda-driver-stubs::cuda-driver-stubs"]
