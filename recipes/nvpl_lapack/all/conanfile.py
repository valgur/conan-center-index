import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplLapackConan(ConanFile):
    name = "nvpl_lapack"
    description = ("NVPL LAPACK (NVIDIA Performance Libraries LAPACK) is part of NVIDIA Performance Libraries"
                   " that provides standard Fortran 90 LAPACK and LAPACKE APIs.")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "lapack", "lapacke", "linear-algebra", "matrix-factorization")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    provides = "lapack"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def requirements(self):
        self.requires("nvpl_blas/[>=0.4 <1]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on Linux")
        if self.settings.arch != "armv8":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on armv8")

    def build(self):
        self._utils.download_cuda_package(self, "nvpl_lapack", platform_id="linux-sbsa")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_lapack")

        def _add_component(name):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            component.set_property("cmake_target_aliases", [name.replace("nvpl_", "nvpl::")])
            component.libs = [name]
            if "ilp64" in name:
                component.defines = ["NVPL_ILP64"]
            component.requires = [f"nvpl_blas::{name.replace('lapack', 'blas')}"]
            if name != "nvpl_lapack_core":
                component.requires.append("nvpl_lapack_core")

        _add_component("nvpl_lapack_core")
        _add_component("nvpl_lapack_lp64_seq")
        _add_component("nvpl_lapack_ilp64_seq")
        _add_component("nvpl_lapack_lp64_gomp")
        _add_component("nvpl_lapack_ilp64_gomp")

        self.cpp_info.components["_prohibit_aggregate_target_"].cflags = ["_dont_use_aggregate_nvpl_lapack_target_"]
