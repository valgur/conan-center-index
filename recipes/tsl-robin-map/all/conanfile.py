from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=2.1"


class TslRobinMapConan(ConanFile):
    name = "tsl-robin-map"
    license = "MIT"
    description = "C++ implementation of a fast hash map and hash set using robin hood hashing."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Tessil/robin-map"
    topics = ("robin-map", "structure", "hash map", "hash set", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tsl-robin-map")
        self.cpp_info.set_property("cmake_target_name", "tsl::robin_map")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
