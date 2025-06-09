from os import path

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "fmi"
    description = "Functional Mock-up Interface (FMI)"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://fmi-standard.org"
    topics = ("fmi-standard", "co-simulation", "model-exchange", "scheduled execution", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def package(self):
        copy(self, "LICENSE.txt", dst=path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*.h",
             path.join(self.source_folder, "headers"),
             path.join(self.package_folder, "include"))
        copy(self, "*.xsd",
             path.join(self.source_folder, "schema"),
             path.join(self.package_folder, "share", self.name))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share/fmi"]
