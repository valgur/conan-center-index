import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SvgPPConan(ConanFile):
    name = "svgpp"
    description = "SVG++ library contains parsers for various SVG syntaxes, " \
                  "adapters that simplify handling of parsed data and a lot of other utilities and helpers for the most common tasks."
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/svgpp/svgpp"
    topics = ("svgpp", "svg", "parser", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]", transitive_headers=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE_1_0.txt", self.source_folderos.path.join(self.package_folder, "licenses"))
        copy(self, "*.*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.requires.append("boost::headers")
