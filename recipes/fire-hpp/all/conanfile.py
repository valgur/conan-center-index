# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.52.0"


class FireHppConan(ConanFile):
    name = "fire-hpp"
    description = "Fire for C++: Create fully functional CLIs using function signatures"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/kongaskristjan/fire-hpp"
    topics = ("command-line", "argument", "parser", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FIRE_EXAMPLES"] = False
        tc.variables["FIRE_UNIT_TESTS"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENCE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
