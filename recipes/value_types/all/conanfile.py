import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class ValueTypesConan(ConanFile):
    name = "value_types"
    description = "a C++20 reference implementation of std::indirect and std::polymophic as a standalone library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/jbcoe/value_types"
    topics = ("utility", "backport")
    package_type = "header-library"
    settings = "os", "arch", "build_type", "compiler"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, "20")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "indirect.h", self.source_folder, os.path.join(self.package_folder, "include"))
        copy(self, "polymorphic.h", self.source_folder, os.path.join(self.package_folder, "include"))
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
