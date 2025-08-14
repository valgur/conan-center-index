import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaxConan(ConanFile):
    name = "cudax"
    description = "CUDA Experimental: Library for experimental features in CUDA Core Compute Libraries"
    license = "Apache-2.0 WITH LLVM-exception"
    homepage = "https://github.com/NVIDIA/cccl/tree/main/cudax"
    topics = ("cuda", "experimental", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        self.requires(f"libcudacxx/{self.version}")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.TXT", os.path.join(self.source_folder, "cudax"), os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "cudax", "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cudax")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["CUDAX"])
        self.cpp_info.set_property("cmake_target_name", "cudax::cudax")

        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
