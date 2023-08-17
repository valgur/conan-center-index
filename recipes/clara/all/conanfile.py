import os
from conan import ConanFile
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout

required_conan_version = ">=1.52.0"


class ClaraConan(ConanFile):
    name = "clara"
    description = "A simple to use, composable, command line parser for C++ 11 and beyond"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/catchorg/Clara"
    topics = ("cli", "cpp11", "command-parser", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    deprecated = "lyra"

    def layout(self):
        basic_layout(self)

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*",
             src=os.path.join(self.source_folder, "include"),
             dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
