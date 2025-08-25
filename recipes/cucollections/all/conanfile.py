import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuCollectionsConan(ConanFile):
    name = "cucollections"
    description = "cuCollections (cuco) is an open-source, header-only library of GPU-accelerated, concurrent data structures"
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/cuCollections"
    topics = ("data-structures", "gpu-acceleration", "concurrent", "stl", "cuda", "nvidia", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        if self.version > "0.0.1+git.20250529":
            # Requires CUDA 13 or higher
            self.requires("cuda-cccl/[^3]")
        else:
            # Requires CUDA 11.5 or higher
            self.requires("cuda-cccl/[^2.5]")
        self.requires(f"cudart/[~{self.settings.cuda.version}]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cuco")
        self.cpp_info.set_property("cmake_target_name", "cuco")
        self.cpp_info.set_property("cmake_target_aliases", ["cuco::cuco"])
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.buildenv_info.append("NVCC_APPEND_FLAGS", "--expt-extended-lambda", separator=" ")
        if stdcpp_library(self):
            self.cpp_info.system_libs = [stdcpp_library(self)]
