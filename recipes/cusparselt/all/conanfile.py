import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuSparseLtConan(ConanFile):
    name = "cusparselt"
    description = "cuSPARSELt: A High-Performance CUDA Library for Sparse Matrix-Matrix Multiplication"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cusparselt/"
    topics = ("cuda", "linear-algebra", "matrix", "sparse")
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
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("cusparse/[^12]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libcusparse_lt")

    def build(self):
        self._utils.download_cuda_package(self, "libcusparse_lt")
        # Fix C compatibility
        replace_in_file(self, os.path.join(self.source_folder, "include", "cusparseLt.h"),
                        "#include <cstddef>",
                        "#include <stddef.h>")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cusparseLt*.dll", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "bin"))
            copy(self, "cusparseLt.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        self.cpp_info.set_property("cmake_target_name", f"CUDA::cusparseLt{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias = "cusparseLt_static" if self.options.shared else "cusparseLt"
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.libs = [f"cusparseLt{suffix}"]
        self.cpp_info.requires = ["cudart::cudart_", "cusparse::cusparse"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
