import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuSolverConan(ConanFile):
    name = "cusolver"
    description = "cuSOLVER: a GPU-accelerated LAPACK-like library on dense and sparse linear algebra"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cusolver/"
    topics = ("cuda", "linear-algebra", "solver", "matrix", "decomposition", "lapack")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
        "cusolverMg": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
        "cusolverMg": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.use_stubs
            self.package_type = "shared-library"

    def configure(self):
        if not self.options.get_safe("shared", True):
            self.options.rm_safe("use_stubs")
            del self.options.cusolverMg

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def requirements(self):
        versions = self._utils.get_cuda_package_versions(self)
        self.requires(f"cudart/[~{versions['cuda_cudart']}]", transitive_headers=True, transitive_libs=True)
        self.requires(f"cublas/[~{versions['libcublas']}]", transitive_headers=True, transitive_libs=True)
        self.requires(f"cusparse/[~{versions['libcusparse']}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libcusolver")
        if self.settings.os == "Linux" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("cusolver requires libstdc++11")

    def build(self):
        self._utils.download_cuda_package(self, "libcusolver")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "libcusolver.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                if self.options.cusolverMg:
                    copy(self, "libcusolverMg.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cusolver*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
            copy(self, "cusolver.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            if self.options.cusolverMg:
                copy(self, "cusolverMg*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
                copy(self, "cusolverMg.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        v = self._cuda_version
        self.cpp_info.components["cusolver_"].set_property("pkg_config_name", f"cusolver-{v.major}.{v.minor}")
        self.cpp_info.components["cusolver_"].set_property("component_version", f"{v.major}.{v.minor}")
        self.cpp_info.components["cusolver_"].set_property("cmake_target_name", f"CUDA::cusolver{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias_suffix = "_static" if self.options.shared else ""
            self.cpp_info.components["cusolver_"].set_property("cmake_target_aliases", [f"CUDA::cusolver{alias_suffix}"])
        self.cpp_info.components["cusolver_"].libs = [f"cusolver{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cusolver_"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["cusolver_"].requires = ["cudart::cudart_", "cublas::cublas_", "cusparse::cusparse"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cusolver_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.components["cusolver_"].requires.append("cudart::culibos")

        if self.options.get_safe("cusolverMg"):
            self.cpp_info.components["cusolverMg"].set_property("cmake_target_name", "CUDA::cusolverMg")
            self.cpp_info.components["cusolverMg"].libs = ["cusolverMg"]
            if self.options.get_safe("use_stubs"):
                self.cpp_info.components["cusolverMg"].libdirs = ["lib/stubs", "lib"]
            self.cpp_info.components["cusolverMg"].requires = ["cudart::cudart_", "cublas::cublas_"]

        # internal components
        if not self.options.get_safe("shared", True):
            self.cpp_info.components["cusolver_lapack"].libs = ["cusolver_lapack_static"]
            self.cpp_info.components["cusolver_metis"].libs = ["cusolver_metis_static"]
            self.cpp_info.components["cusolver_metis"].requires = ["metis"]
            self.cpp_info.components["metis"].libs = ["metis_static"]
            self.cpp_info.components["cusolver_"].requires.extend(["cusolver_lapack", "cusolver_metis"])
