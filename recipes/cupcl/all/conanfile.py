import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuPclConan(ConanFile):
    name = "cupcl"
    description = "cuPCL: CUDA point cloud libraries by Nvidia"
    license = "MIT"
    homepage = "https://github.com/NVIDIA-AI-IOT/cuPCL"
    topics = ("cuda", "point-cloud", "lidar", "nvidia")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        del self.info.settings.cuda.platform

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("eigen/3.4.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Only Linux is supported")
        if self.settings.arch == "x86_64":
            if "x86_64" not in self.version:
                raise ConanInvalidConfiguration(f"{self.ref} version does not support x86_64")
        elif self.settings.arch == "armv8":
            if "jp" not in self.version and "armv8" not in self.version:
                raise ConanInvalidConfiguration(f"{self.ref} version does not support armv8")
        else:
            raise ConanInvalidConfiguration(f"{self.settings.arch} is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        for lib_dir in Path(self.source_folder).rglob("lib"):
            copy(self, "*.h", lib_dir, os.path.join(self.package_folder, "include"))
            copy(self, "*.so*", lib_dir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        for lib in [
            "cudacluster",
            "cudafilter",
            "cudaicp",
            "cudandt",
            "cudaoctree",
            "cudasegmentation",
        ]:
            self.cpp_info.components[lib].libs = [lib]
            self.cpp_info.components[lib].requires = ["cudart::cudart_", "eigen::eigen"]
