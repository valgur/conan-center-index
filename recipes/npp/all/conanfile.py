import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NppConan(ConanFile):
    name = "npp"
    description = "NPP: NVIDIA 2D Image and Signal Processing Performance Primitives libraries"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/npp/"
    topics = ("cuda", "image-processing", "signal-processing", "performance-primitives")
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
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def requirements(self):
        versions = self._utils.get_cuda_package_versions(self)
        self.requires(f"cudart/[~{versions['cuda_cudart']}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libnpp")

    def build(self):
        self._utils.download_cuda_package(self, "libnpp")

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
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        v = self._cuda_version
        for name in [
            "nppc",    # Core
            "nppial",  # Image Analysis
            "nppicc",  # Image Color Conversion
            "nppidei", # Image Data Exchange and Initialization
            "nppif",   # Image Filtering
            "nppig",   # Image Geometry
            "nppim",   # Image Morphology
            "nppist",  # Image Statistics
            "nppisu",  # Image Signal Utilities
            "nppitc",  # Image Threshold and Compare
            "npps",    # Signal Processing
        ]:
            component = self.cpp_info.components[name]
            component.set_property("pkg_config_name", f"{name}-{v.major}.{v.minor}")
            component.set_property("component_version", f"{v.major}.{v.minor}")
            component.set_property("cmake_target_name", f"CUDA::{name}{suffix}")
            if self.options.get_safe("cmake_alias"):
                component.set_property("cmake_target_aliases", [f"CUDA::{name}{alias_suffix}"])
            component.libs = [f"{name}{suffix}"]
            if self.options.get_safe("use_stubs"):
                component.libdirs = ["lib/stubs", "lib"]
            component.requires = ["cudart::cudart_"]
            if name != "nppc":
                component.requires.append("nppc")
            if self.settings.os == "Linux" and not self.options.shared:
                component.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
                component.requires.append("cudart::culibos")

        # Unofficial aggregate target for Image Processing
        self.cpp_info.components["nppi"].set_property("pkg_config_name", f"nppi-{v.major}.{v.minor}")
        self.cpp_info.components["nppi"].set_property("component_version", f"{v.major}.{v.minor}")
        self.cpp_info.components["nppi"].set_property("cmake_target_name", f"CUDA::nppi{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["nppi"].set_property("cmake_target_aliases", [f"CUDA::nppi{alias_suffix}"])
        self.cpp_info.components["nppi"].requires = ["nppial", "nppicc", "nppidei", "nppif", "nppig", "nppim", "nppist", "nppisu", "nppitc"]
