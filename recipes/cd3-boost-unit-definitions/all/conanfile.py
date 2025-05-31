import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class Cd3BoostUnitDefinitionsConan(ConanFile):
    name = "cd3-boost-unit-definitions"
    description = "A collection of pre-defined types and unit instances for working with Boost.Units quantities."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CD3/BoostUnitDefinitions"
    topics = ("physical dimensions", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "BoostUnitDefinitions")
        self.cpp_info.set_property("cmake_target_name", "BoostUnitDefinitions::BoostUnitDefinitions")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
