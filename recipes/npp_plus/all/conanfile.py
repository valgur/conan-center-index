import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NppPlusConan(ConanFile):
    name = "npp_plus"
    description = "NPP+: NVIDIA C++ 2D Image and Signal Processing Performance Primitives Library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/nppplus/"
    topics = ("cuda", "image-processing", "signal-processing", "performance-primitives")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
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

    # Provides NPP headers and symbols
    provides = ["npp"]

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
        if not self.options.shared:
            self.requires(f"culibos/[~{self.settings.cuda.version}]")

    def validate(self):
        self._utils.validate_cuda_package(self, "libnpp_plus")

    def build(self):
        self._utils.download_cuda_package(self, "libnpp_plus")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # The CMake file and target names are not official
        self.cpp_info.set_property("cmake_file_name", "nppPlus")
        self.cpp_info.set_property("cmake_target_name", "nppPlus::nppPlus")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        for name in [
            "npp_plus_c", # Core library
            "npp_plus_ial", # Arithmetic and logical operation
            "npp_plus_icc", # Color conversion and sampling
            "npp_plus_idei", # Data exchange and initialization
            "npp_plus_if", # Filtering and computer vision
            "npp_plus_ig", # Geometry transformation
            "npp_plus_im", # Morphological operations
            "npp_plus_ist", # Statistics and linear transforms
            "npp_plus_isu", # Memory support
            "npp_plus_itc", # Threshold and compare operations
            "npp_plus_s", # Signal processing
            "npp_plus_ai", # ???
            "npp_plus_as", # ???
        ]:
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", f"nppPlus::{name}{suffix}")
            if self.options.get_safe("cmake_alias"):
                component.set_property("cmake_target_aliases", [f"nppPlus::{name}{alias_suffix}"])
            component.libs = [f"{name}{suffix}"]
            if self.options.get_safe("use_stubs"):
                component.libdirs = ["lib/stubs", "lib"]
            component.requires = ["cudart::cudart_"]
            if name != "npp_plus_c":
                component.requires.append("npp_plus_c")
            if self.settings.os == "Linux" and not self.options.shared:
                component.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
                component.requires.append("culibos::culibos")

        self.cpp_info.components["npp_plus_i"].set_property("cmake_target_name", f"nppPlus::npp_plus_i{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["npp_plus_i"].set_property("cmake_target_aliases", [f"nppPlus::npp_plus_i{alias_suffix}"])
        self.cpp_info.components["npp_plus_i"].requires = [
            name for name, _ in self.cpp_info.components.items() if name.startswith("npp_plus_i") and name != "npp_plus_i"
        ]
