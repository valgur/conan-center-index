import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuTensorConan(ConanFile):
    name = "cutensor"
    description = "cuTENSOR: A High-Performance CUDA Library For Tensor Primitives"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cutensor/"
    topics = ("cuda", "tensor", "linear-algebra", "deep-learning", "multi-gpu")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "cutensorMg": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "cutensorMg": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if Version(self.version) >= "2.3":
            if self.settings.os == "Windows":
                del self.options.shared
                self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.requires(f"cublas/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libcutensor")
        cuda_version = Version(self.settings.cuda.version)
        if Version(self.version) < "2.3" and cuda_version >= "13":
            raise ConanInvalidConfiguration(f"{self.ref} requires CUDA < 13, but cuda.version={self.settings.cuda.version}")
        if self.options.get_safe("shared", True):
            self._utils.require_shared_deps(self, ["cublas"])

    def build(self):
        self._utils.download_cuda_package(self, "libcutensor")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if Version(self.version) >= "2.3":
            lib_dir = os.path.join(self.source_folder, "lib")
            bin_dir = os.path.join(self.source_folder, "bin")
        else:
            cuda_ver = str(Version(self.settings.cuda.version).major) if Version(self.settings.cuda.version) != "11.0" else "11.0"
            lib_dir = os.path.join(self.source_folder, "lib", cuda_ver)
            bin_dir = lib_dir

        def copy_lib(name):
            if self.settings.os == "Linux":
                if self.options.shared:
                    copy(self, f"lib{name}.so*", lib_dir, os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"lib{name}_static.a", lib_dir, os.path.join(self.package_folder, "lib"))
            else:
                if self.options.get_safe("shared", True):
                    copy(self, f"{name}.dll", bin_dir, os.path.join(self.package_folder, "bin"))
                    copy(self, f"{name}.lib", lib_dir, os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"{name}_static.lib", lib_dir, os.path.join(self.package_folder, "lib"))

        copy_lib("cutensor")
        if self.options.cutensorMg:
            copy_lib("cutensorMg")

    def package_info(self):
        # The CMake target names are not an official part of the package or FindCUDAToolkit.cmake

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""

        self.cpp_info.components["cutensor_"].set_property("cmake_target_name", f"CUDA::cutensor{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["cutensor_"].set_property("cmake_target_aliases", [f"CUDA::cutensor{alias_suffix}"])
        self.cpp_info.components["cutensor_"].libs = [f"cutensor{suffix}"]
        self.cpp_info.components["cutensor_"].requires = ["cublas::cublasLt"]

        if self.options.cutensorMg:
            self.cpp_info.components["cutensorMg"].set_property("cmake_target_name", f"CUDA::cutensorMg{suffix}")
            if self.options.get_safe("cmake_alias"):
                self.cpp_info.components["cutensorMg"].set_property("cmake_target_aliases", [f"CUDA::cutensorMg{alias_suffix}"])
            self.cpp_info.components["cutensorMg"].libs = [f"cutensorMg{suffix}"]
            self.cpp_info.components["cutensorMg"].requires = ["cutensor_"]
