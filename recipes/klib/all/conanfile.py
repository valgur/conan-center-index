import os
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class KlibConan(ConanFile):
    name = "klib"
    description = "Klib: a Generic Library in C"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/project/package"
    topics = ("algorithm", "avl-tree", "generic", "sorting", "hashtable", "b-tree")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "header_only": [True, False],
        "prefixed_headers": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "header_only": True,
        "prefixed_headers": False,
    }
    implements = ["auto_shared_fpic", "auto_header_only"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not self.options.header_only:
            tc = CMakeToolchain(self)
            tc.generate()

    def build(self):
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if self.options.header_only:
            for path in Path(self.source_folder).glob("*.h"):
                if not path.with_suffix(".c").exists():
                    copy(self, path.name, self.source_folder, os.path.join(self.package_folder, "include", "klib"))
        else:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        if not self.options.prefixed_headers:
            self.cpp_info.includedirs.append(os.path.join("include", "klib"))
        if self.options.header_only:
            self.cpp_info.bindirs = []
            self.cpp_info.libdirs = []
        else:
            self.cpp_info.libs = ["klib"]
