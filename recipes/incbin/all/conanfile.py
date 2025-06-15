import os

from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMakeToolchain, CMake
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class IncbinConan(ConanFile):
    name = "incbin"
    description = "Include binary files in C/C++"
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/graphitemaster/incbin/"
    topics = ("include", "binary", "preprocess")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def config_options(self):
        if is_msvc(self):
            self.package_type = "static-library"

    def package_id(self):
        if self.package_type == "header-library":
            self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if is_msvc(self):
            tc = CMakeToolchain(self)
            tc.generate()

    def build(self):
        if is_msvc(self):
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "UNLICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "incbin.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)

        if is_msvc(self):
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        self.cpp_info.libdirs = []
        if not is_msvc(self):
            self.cpp_info.bindirs = []
