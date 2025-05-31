import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"

class FakeItConan(ConanFile):
    name = "fakeit"
    description = "C++ mocking made easy. A simple yet very expressive, headers only library for c++ mocking."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/eranpeer/FakeIt"
    topics = ("mock", "fake", "spy", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "integration": ["standalone", "boost", "catch", "cute", "gtest", "mettle", "nunit", "mstest", "qtest", "tpunit"],
    }
    default_options = {
        "integration": "standalone",
    }
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.integration == "boost":
            self.requires("boost/[^1.71.0]", options={"with_test": True})
        elif self.options.integration == "catch":
            self.requires("catch2/[^3.5.2]")
        elif self.options.integration == "gtest":
            self.requires("gtest/[^1.14.0]")
        elif self.options.integration == "qtest":
            self.requires("qt/[>=6.6 <7]")
        elif self.options.integration == "standalone":
            pass
        else:
            raise ConanInvalidConfiguration("%s is not (yet) available on cci" % self.options.integration)

    def package_id(self):
        # The "integration" option must be kept because it will impact which header is packaged,
        # therefor self.info.clear() cannot be used.
        self.info.settings.clear()
        self.info.requires.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "fakeit.hpp",
             os.path.join(self.source_folder, "single_header", str(self.options.integration)),
             os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
