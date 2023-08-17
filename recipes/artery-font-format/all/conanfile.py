import os

from conan import ConanFile
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout

required_conan_version = ">=1.52.0"


class ArteryFontFormatConan(ConanFile):
    name = "artery-font-format"
    description = "Artery Atlas Font format library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Chlumsky/artery-font-format"
    topics = ("artery", "font", "atlas", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        # header only: no build step
        pass

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*.h",
             dst=os.path.join(self.package_folder, "include"),
             src=self.source_folder)
        copy(self, "*.hpp",
             dst=os.path.join(self.package_folder, "include"),
             src=self.source_folder)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
