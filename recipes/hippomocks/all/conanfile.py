# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout

required_conan_version = ">=1.52.0"


class HippomocksConan(ConanFile):
    name = "hippomocks"
    description = "Single-header mocking framework."
    license = "LGPL-2.1"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dascandy/hippomocks"
    topics = ("mock", "framework", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _libname(self):
        return "HippoMocks"

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*.h",
            dst=os.path.join("include", self._libname),
            src=os.path.join(self.source_folder, self._libname),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
