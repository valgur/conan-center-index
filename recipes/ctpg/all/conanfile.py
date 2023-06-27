# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class CTPGConan(ConanFile):
    name = "ctpg"
    description = (
        "Compile Time Parser Generator is a C++ single header library which takes a language description as a"
        " C++ code and turns it into a LR1 table parser with a deterministic finite automaton lexical"
        " analyzer, all in compile time."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/peter-winter/ctpg"
    topics = ("regex", "parser", "grammar", "compile-time", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        ## TODO: In ctpg<=1.3.5, Visual Studio C++ failed to compile ctpg with "error MSB6006: "CL.exe" exited with code -1073741571."
        if is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.name} does not support Visual Studio currently.")

        if self.settings.get_safe("compiler.cppstd"):
            check_min_cppstd(self, "17")

        minimum_version = self._compiler_required_cpp17.get(str(self.settings.compiler), False)
        if minimum_version:
            if Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "{} requires C++17, which your compiler does not support.".format(self.name)
                )
        else:
            self.output.warn(
                "{} requires C++17. Your compiler is unknown. Assuming it supports C++17.".format(self.name)
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", "licenses", self.source_folder)
        if Version(self.version) >= "1.3.7":
            copy(
                self,
                "ctpg.hpp",
                os.path.join("include", "ctpg"),
                os.path.join(self.source_folder, "include", "ctpg"),
            )
        else:
            copy(self, "ctpg.hpp", "include", os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
