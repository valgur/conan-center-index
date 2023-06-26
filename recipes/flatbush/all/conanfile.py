# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import valid_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout

required_conan_version = ">=1.52.0"


class FlatbushConan(ConanFile):
    name = "flatbush"
    description = "Flatbush for C++"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/chusitoo/flatbush"
    topics = ("header-only", "r-tree", "hilbert", "zero-copy", "spatial-index")

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
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"))
        copy(self, pattern="flatbush.h", dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if not valid_min_cppstd(self, "20"):
            self.cpp_info.defines = ["FLATBUSH_SPAN"]
