from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=2.1"


class RingSpanLiteConan(ConanFile):
    name = "ring-span-lite"
    description = (
        "ring-span lite - A ring_span type for C++98, C++11 and later in a single-file header-only library ")
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/martinmoene/ring-span-lite"
    topics = ("cpp98", "cpp11", "cpp14", "cpp17", "ring-span", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def package_id(self):
        self.info.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "*.hpp", src=os.path.join(self.source_folder, "include"),
             dst=os.path.join(self.package_folder, "include"))
        copy(self, "LICENSE.txt", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ring-span-lite")
        self.cpp_info.set_property("cmake_target_name", "nonstd::ring-span-lite")
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
