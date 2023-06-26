# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class EnhexGenericserializationConan(ConanFile):
    name = "enhex-generic_serialization"
    description = "Lightweight and extensible generic serialization library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Enhex/generic_serialization"
    topics = ("serialization", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        minimal_version = {
            "Visual Studio": "15",
            "gcc": "7",
            "clang": "5.0",
            "apple-clang": "9.1",
        }
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)

        if compiler not in minimal_version:
            self.output.info("{} requires a compiler that supports at least C++17".format(self.name))
            return

        # Exclude compilers not supported
        if compiler_version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                f"{self.name} requires a compiler that supports at least C++17."
                f" {compiler} {Version(self.settings.compiler.version.value)} is not"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            pattern="LICENSE.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
