import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MBitsArgsConan(ConanFile):
    name = "mbits-args"
    description = (
        "Small open-source library for program argument parser, inspired by Python's `argparse`, "
        "depending only on the standard library, with C++17 as minimum requirement."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mbits-libs/args"
    topics = (
        "command-line",
        "commandline",
        "commandline-interface",
        "program-arguments",
        "argparse",
        "argparser",
        "argument-parsing",
    )
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIBARGS_TESTING"] = False
        tc.variables["LIBARGS_INSTALL"] = True
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
        self.cpp_info.set_property("cmake_file_name", "mbits-args")
        self.cpp_info.set_property("cmake_target_name", "mbits::args")
        self.cpp_info.libs = ["args"]
