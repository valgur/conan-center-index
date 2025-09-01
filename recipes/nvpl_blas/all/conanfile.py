import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplBlasConan(ConanFile):
    name = "nvpl_blas"
    description = ("NVPL BLAS (NVIDIA Performance Libraries BLAS) is part of NVIDIA Performance Libraries"
                   " that provides standard Fortran 77 BLAS APIs as well as C (CBLAS).")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "blas", "linear-algebra")
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
        self.cuda.download_package("nvpl_blas", platform_id="linux-sbsa")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_blas")

        def _add_component(name):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            component.set_property("cmake_target_aliases", [name.replace("nvpl_", "nvpl::")])
            component.libs = [name]
            if "ilp64" in name:
                component.defines = ["NVPL_ILP64"]
            if name != "nvpl_blas_core":
                component.requires = ["nvpl_blas_core"]

        _add_component("nvpl_blas_core")
        _add_component("nvpl_blas_lp64_seq")
        _add_component("nvpl_blas_ilp64_seq")
        _add_component("nvpl_blas_lp64_gomp")
        _add_component("nvpl_blas_ilp64_gomp")

        self.cpp_info.components["_prohibit_aggregate_target_"].cflags = ["_dont_use_aggregate_nvpl_blas_target_"]
