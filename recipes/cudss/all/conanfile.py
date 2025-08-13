import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuDssConan(ConanFile):
    name = "cudss"
    description = "NVIDIA cuDSS is a library of GPU-accelerated linear solvers with sparse matrices"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cudss/"
    topics = ("cuda", "linear-algebra", "sparse-matrix", "direct-solver")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "commlayer_nccl": [True, False],
        "commlayer_mpi": [True, False],
        "mtlayer_omp": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "commlayer_nccl": False,
        "commlayer_mpi": False,
        "mtlayer_omp": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"
        if self.settings.os != "Linux":
            del self.options.commlayer_nccl
            del self.options.commlayer_mpi

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")

    @cached_property
    def _cuda_version(self):
        return self.dependencies["cudart"].ref.version

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires(f"cublas/[~{self.settings.cuda.version}]")
        if self.options.commlayer_nccl:
            self.requires("nccl/[^2]")
        if self.options.commlayer_mpi:
            self.requires("openmpi/[>=4 <6]")
        # gomp or vcomp140 from the system is required for OpenMP support

    def validate(self):
        self._utils.validate_cuda_package(self, "libcudss")
        if self.options.get_safe("shared", True):
            self._utils.require_shared_deps(self, ["cublas", "nccl", "openmpi"])

    def build(self):
        self._utils.download_cuda_package(self, "libcudss")
        # TODO: build the commlayer and mtlayer components from the provided sources

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "share", "cudss", "src"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "libcudss.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "libcudss_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.commlayer_nccl:
                copy(self, "libcudss_commlayer_nccl.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.commlayer_mpi:
                copy(self, "libcudss_commlayer_openmpi.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.mtlayer_omp:
                copy(self, "libcudss_mtlayer_gomp.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cudss.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            copy(self, "cudss64_*.dll", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "bin"))
            if self.options.mtlayer_omp:
                copy(self, "cudss_mtlayer_vcomp140.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "cudss_mtlayer_vcomp140.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        # The package exports a CMake config with cudss and cudss_static targets.
        self.cpp_info.set_property("cmake_file_name", "cudss")
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        self.cpp_info.components["cudss_"].set_property("cmake_target_name", f"cudss{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["cudss_"].set_property("cmake_target_aliases", [f"cudss{alias_suffix}"])
        self.cpp_info.components["cudss_"].libs = [f"cudss{suffix}"]
        self.cpp_info.components["cudss_"].requires = ["cudart::cudart_", "cublas::cublas_"]
        self.cpp_info.components["cudss_"].srcdirs = ["share/cudss/src"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cudss_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]

        # These target names are not officially provided
        if self.settings.os == "Linux":
            if self.options.commlayer_nccl:
                self.cpp_info.components["cudss_commlayer_nccl"].set_property("cmake_target_name", "cudss_commlayer_nccl")
                self.cpp_info.components["cudss_commlayer_nccl"].libs = ["cudss_commlayer_nccl"]
                self.cpp_info.components["cudss_commlayer_nccl"].requires = ["nccl::nccl"]
            if self.options.commlayer_mpi:
                self.cpp_info.components["cudss_commlayer_mpi"].set_property("cmake_target_name", "cudss_commlayer_mpi")
                self.cpp_info.components["cudss_commlayer_mpi"].libs = ["cudss_commlayer_openmpi"]
                self.cpp_info.components["cudss_commlayer_mpi"].requires = ["openmpi::openmpi"]
        if self.options.mtlayer_omp:
            self.cpp_info.components["cudss_mtlayer_omp"].set_property("cmake_target_name", "cudss_mtlayer_omp")
            self.cpp_info.components["cudss_mtlayer_omp"].libs = ["cudss_mtlayer_gomp" if self.settings.os == "Linux" else "cudss_mtlayer_vcomp140"]
            self.cpp_info.components["cudss_mtlayer_omp"].system_libs = ["gomp"]
