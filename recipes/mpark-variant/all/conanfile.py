from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=2.1"


class MparkVariantConan(ConanFile):
    name = "mpark-variant"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mpark/variant"
    description = "C++17 std::variant for C++11/14/17"
    license = "BSL-1.0"
    topics = ("variant", "mpark-variant")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mpark_variant")
        self.cpp_info.set_property("cmake_target_name", "mpark_variant")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
