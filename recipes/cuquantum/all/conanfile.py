import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuQuantumConan(ConanFile):
    name = "cuquantum"
    description = ("NVIDIA cuQuantum is an SDK of optimized libraries and tools that accelerate"
                   " quantum computing emulations at both the circuit and device level by orders of magnitude")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cuquantum"
    topics = ("cuda", "quantum-computing", "simulation", "nvidia")
    # static is also supported but requires an additional ExaTN dependency for cutensornet
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

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
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
        self._utils.cuda_requires(self, "cusolver")
        self._utils.cuda_requires(self, "cublas")
        self._utils.cuda_requires(self, "cusparse")
        self._utils.cuda_requires(self, "nvjitlink")
        self.requires("cutensor/[^2]")

    def validate(self):
        self._utils.validate_cuda_package(self, "cuquantum")
        if self.options.get_safe("shared", True):
            self._utils.require_shared_deps(self, ["cutensor", "cusolver", "cublas", "cusparse", "nvjitlink"])

    def build(self):
        self._utils.download_cuda_package(self, "cuquantum")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.options.get_safe("shared", True):
            copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # The CMake config and target names are not official
        self.cpp_info.set_property("cmake_file_name", "cuQuantum")
        self.cpp_info.set_property("cmake_target_name", "cuQuantum::cuQuantum")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""

        self.cpp_info.components["cudensitymat"].set_property("cmake_target_name", f"cuQuantum::cudensitymat{suffix}")
        self.cpp_info.components["cudensitymat"].set_property("cmake_target_aliases", [f"cuQuantum::cudensitymat{alias_suffix}"])
        self.cpp_info.components["cudensitymat"].libs = [f"cudensitymat{suffix}"]
        self.cpp_info.components["cudensitymat"].requires = [
            "cutensornet",
            "cudart::cudart_",
            "cutensor::cutensor_",
            "cusolver::cusolver_",
            "cublas::cublas_",
            "cusparse::cusparse",
            "nvjitlink::nvjitlink",
        ]

        self.cpp_info.components["custatevec"].set_property("cmake_target_name", f"cuQuantum::custatevec{suffix}")
        self.cpp_info.components["custatevec"].set_property("cmake_target_aliases", [f"cuQuantum::custatevec{alias_suffix}"])
        self.cpp_info.components["custatevec"].libs = [f"custatevec{suffix}"]
        self.cpp_info.components["custatevec"].requires = [
            "cudart::cudart_",
            "cublas::cublas_",
        ]

        self.cpp_info.components["cutensornet"].set_property("cmake_target_name", f"cuQuantum::cutensornet{suffix}")
        self.cpp_info.components["cutensornet"].set_property("cmake_target_aliases", [f"cuQuantum::cutensornet{alias_suffix}"])
        self.cpp_info.components["cutensornet"].libs = [f"cutensornet{suffix}"]
        self.cpp_info.components["cutensornet"].requires = [
            "cudart::cudart_",
            "cutensor::cutensor_",
            "cublas::cublas_",
            "cusolver::cusolver_",
        ]
        if not self.options.get_safe("shared", True):
            self.cpp_info.components["cutensornet"].system_libs = ["m", "pthread", "dl", "rt", "stdc++", "gcc_s"]
