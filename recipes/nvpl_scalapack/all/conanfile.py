import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplScalapackConan(ConanFile):
    name = "nvpl_scalapack"
    description = "NVPL ScaLAPACK provides an optimized implementation of ScaLAPACK for distributed-memory architectures."
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "scalapack", "linear-algebra", "distributed-computing")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    provides = "scalapack"
    options = {
        "with_openmpi": [True, False],
        "with_mpich": [True, False],
    }
    default_options = {
        "with_openmpi": True,
        "with_mpich": False,
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

    def requirements(self):
        self.requires("nvpl_lapack/[>=0.3 <1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmpi:
            self.requires("openmpi/[>=3 <6]", transitive_headers=True, transitive_libs=True)
        # TODO: add mpich

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on Linux")
        if self.settings.arch != "armv8":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on armv8")
        self._utils.require_shared_deps(self, ["openmpi"])

    def build(self):
        self._utils.download_cuda_package(self, "nvpl_scalapack", platform_id="linux-sbsa")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "libnvpl_scalapack_*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        if self.options.with_openmpi:
            openmpi_major = self.dependencies["openmpi"].ref.version.major
            copy(self, f"libnvpl_blacs_*_openmpi{openmpi_major}.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        if self.options.with_mpich:
            copy(self, "libnvpl_blacs_*_mpich.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_scalapack")

        def _add_component(name):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            aliases = [name.replace("nvpl_", "nvpl::")]
            if "openmpi" in name:
                # without version suffix
                aliases.append(name.replace("nvpl_", "nvpl::")[:-1])
            component.set_property("cmake_target_aliases", aliases)
            component.libs = [name]
            component.requires = ["nvpl_lapack::nvpl_lapack_core"]
            if "openmpi" in name:
                component.requires.append("openmpi::openmpi")

        _add_component("nvpl_scalapack_lp64")
        _add_component("nvpl_scalapack_ilp64")

        if self.options.with_openmpi:
            openmpi_major = self.dependencies["openmpi"].ref.version.major
            _add_component(f"nvpl_blacs_lp64_openmpi{openmpi_major}")
            _add_component(f"nvpl_blacs_ilp64_openmpi{openmpi_major}")

        if self.options.with_mpich:
            _add_component(f"nvpl_blacs_lp64_mpich")
            _add_component(f"nvpl_blacs_ilp64_mpich")

        self.cpp_info.components["nvpl_scalapack_public_headers"].set_property("cmake_target_name", "nvpl_scalapack_public_headers")
        self.cpp_info.components["nvpl_scalapack_public_headers"].includedirs = ["include"]
        self.cpp_info.components["nvpl_scalapack_public_headers"].libdirs = []

        self.cpp_info.components["_prohibit_aggregate_target_"].cflags = ["_dont_use_aggregate_nvpl_scalapack_target_"]
