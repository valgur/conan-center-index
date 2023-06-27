# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get, rename
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class AclConan(ConanFile):
    name = "nfrechette-acl"
    description = "Animation Compression Library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/nfrechette/acl"
    topics = ("animation", "compression", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def configure(self):
        minimal_cpp_standard = "11"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration(
                f"acl can't be compiled by {self.settings.compiler} {self.settings.compiler.version}"
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rtm/2.1.4")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "acl-" + self.version
        rename(self, extracted_dir, self.source_folder)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "includes"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
