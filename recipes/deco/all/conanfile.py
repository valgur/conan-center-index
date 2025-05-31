import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class DecoConan(ConanFile):
    name = "deco"
    description = "Delimiter Collision Free Format"
    license = "Apache-2.0-WITH-LLVM-exception"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Enhex/Deco"
    topics = ("serialization", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("enhex-generic_serialization/1.0.0")
        self.requires("enhex-strong_type/1.0.0")
        self.requires("boost/[^1.71.0]")
        self.requires("rang/3.2")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "*",
             dst=os.path.join(self.package_folder, "include"),
             src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
