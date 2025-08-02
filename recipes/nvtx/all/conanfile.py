import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NVTXConan(ConanFile):
    name = "nvtx"
    description = (
        "The NVIDIA Tools Extension SDK (NVTX) is a C-based API for annotating "
        "events, code ranges, and resources in your applications."
    )
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/NVTX"
    topics = ("nvidia", "profiler", "nsight")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "c", "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvtx3")
        self.cpp_info.set_property("cmake_target_name", "nvtx3::nvtx3-c")
        self.cpp_info.set_property("cmake_target_aliases", ["nvtx3::nvtx3-cpp", "CUDA::nvtx3"])
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl"]
