# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.52.0"


class JsonformoderncppConan(ConanFile):
    name = "jsonformoderncpp"
    description = "JSON for Modern C++ parser and generator."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/nlohmann/json"
    topics = ("json", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "multiple_headers": [True, False],
    }
    default_options = {
        "multiple_headers": False,
    }
    no_copy_source = True
    deprecated = "nlohmann_json"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["JSON_BuildTests"] = False
        tc.variables["JSON_MultipleHeaders"] = self.options.multiple_headers
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))
        try:
            os.remove(os.path.join(self.package_folder, "nlohmann_json.natvis"))
        except FileNotFoundError:
            pass

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
