import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class OptixHeadersConan(ConanFile):
    name = "optix-headers"
    description = "OptiX SDK headers, everything needed to build & run OptiX applications"
    license = "DocumentRef-LICENSE.txt:LicenseRef-NvidiaProprietary"
    homepage = "https://github.com/NVIDIA/optix-dev"
    topics = ("gpu", "cuda", "nvidia", "gpu-acceleration", "ray-tracing", "optix", "gpu-programming", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        self.requires(f"cuda-driver-stubs/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
