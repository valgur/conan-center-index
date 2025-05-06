import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MBitsMstchConan(ConanFile):
    name = "mbits-mstch"
    description = "libmstch implemented in terms of C++17 variant."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mbits-libs/libmstch"
    topics = ("parser", "mstch", "mustache", "libmstch", "libmstch-parser")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.0.2)",
                        "cmake_minimum_required(VERSION 3.15)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mbits-mstch")
        self.cpp_info.set_property("cmake_target_name", "mbits::mstch")
        self.cpp_info.libs = ["mstch"]
