import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.18"


class CublasConan(ConanFile):
    name = "cublas"
    description = "CUDA Basic Linear Algebra Subprograms"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cublas"
    topics = ("cuda", "blas", "linear-algebra")
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
            del self.options.shared
            self.package_type = "shared-library"

    def configure(self):
        if self.settings.os == "Windows" or not self.options.get_safe("shared", True):
            del self.options.use_stubs

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.options.cmake_alias

    def requirements(self):
        v = Version(self.version)
        self.requires(f"cudart/[~{v.major}.{v.minor}]", transitive_headers=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libcublas")
        if self.settings.os == "Linux" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("cublas requires libstdc++11 on Linux")

    def package(self):
        self._utils.download_cuda_package(self, "libcublas", destination=self.package_folder)
        mkdir(self, os.path.join(self.package_folder, "licenses"))
        os.rename(os.path.join(self.package_folder, "LICENSE"), os.path.join(self.package_folder, "licenses", "LICENSE"))
        rmdir(self, os.path.join(self.package_folder, "pkg-config"))
        if self.settings.os == "Linux":
            if self.options.shared:
                rm(self, "libcublas_static.a", os.path.join(self.package_folder, "lib"))
                rm(self, "libcublasLt_static.a", os.path.join(self.package_folder, "lib"))
            else:
                rm(self, "libcublas.so*", os.path.join(self.package_folder, "lib"))
                rm(self, "libcublasLt.so*", os.path.join(self.package_folder, "lib"))
        else:
            move_folder_contents(self, os.path.join(self.package_folder, "lib", "x64"),
                                 os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "none")

        v = Version(self.version)
        lib = "cublas" if self.options.shared else "cublas_static"
        self.cpp_info.components["cublas_"].set_property("cmake_target_name", f"CUDA::{lib}")
        if self.options.cmake_alias:
            alias = "cublas_static" if self.options.get_safe("shared", True) else "cublas"
            self.cpp_info.components["cublas_"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cublas_"].set_property("pkg_config_name", f"cublas-{v.major}.{v.minor}")
        self.cpp_info.components["cublas_"].set_property("component_version", f"{v.major}.{v.minor}")
        self.cpp_info.components["cublas_"].libs = [lib]
        self.cpp_info.components["cublas_"].srcdirs = ["share/cublas/src"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cublas_"].libdirs = ["lib/stubs", "lib"]
        if self.settings.os == "Linux":
            self.cpp_info.components["cublas_"].system_libs = ["dl", "m", "pthread", "rt"]
            self.cpp_info.components["cublas_"].requires = ["cublasLt"]

        lib = "cublasLt" if self.options.get_safe("shared", True) else "cublasLt_static"
        self.cpp_info.components["cublasLt"].set_property("cmake_target_name", f"CUDA::{lib}")
        if self.options.cmake_alias:
            alias = "cublasLt_static" if self.options.get_safe("shared", True) else "cublasLt"
            self.cpp_info.components["cublasLt"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cublasLt"].libs = [lib]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cublasLt"].libdirs = ["lib/stubs", "lib"]
        if self.settings.os == "Linux":
            self.cpp_info.components["cublasLt"].system_libs = ["dl", "m", "pthread", "rt", "stdc++"]
        self.cpp_info.components["cublasLt"].requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cublasLt"].requires.append("cudart::culibos")

        self.cpp_info.components["nvblas"].set_property("cmake_target_name", "CUDA::nvblas")
        self.cpp_info.components["nvblas"].libs = ["nvblas"]
        self.cpp_info.components["nvblas"].requires = ["cublas_"]
