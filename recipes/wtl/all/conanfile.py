from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.54.0"


class WTLConan(ConanFile):
    name = "wtl"
    description = (
        "Windows Template Library (WTL) is a C++ library for "
        "developing Windows applications and UI components."
    )
    license = "MS-PL"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sourceforge.net/projects/wtl"
    topics = ("atl", "template library", "windows", "template", "ui", "gdi", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration(f"{self.ref} can only be used on Windows.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "MS-PL.TXT", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(
            self,
            "*",
            src=os.path.join(self.source_folder, "include"),
            dst=os.path.join(self.package_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
