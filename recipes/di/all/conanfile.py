# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class DiConan(ConanFile):
    name = "di"
    description = "DI: C++14 Dependency Injection Library."
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/boost-ext/di"
    topics = ("dependency-injection", "metaprogramming", "design-patterns", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_extensions": [True, False],
        "diagnostics_level": [0, 1, 2],
    }
    default_options = {
        "with_extensions": False,
        "diagnostics_level": 1,
    }
    no_copy_source = True

    def export_sources(self):
        copy(self, "BSL-1.0.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def configure(self):
        minimal_cpp_standard = "14"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)
        minimal_version = {
            "gcc": "5",
            "clang": "3.4",
            "apple-clang": "10",
            "Visual Studio": "15",
        }
        compiler = str(self.settings.compiler)
        if compiler not in minimal_version:
            self.output.warning(
                "%s recipe lacks information about the %s compiler standard version support"
                % (self.name, compiler)
            )
            self.output.warning(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )
            return
        version = Version(self.settings.compiler.version)
        if version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.requires.clear()
        self.info.settings.clear()
        del self.info.options.diagnostics_level

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "BSL-1.0.txt", src="", dst=os.path.join(self.package_folder, "licenses"))
        if self.options.with_extensions:
            copy(
                self,
                "*.hpp",
                src=os.path.join(self.source_folder, "extension", "include", "boost", "di", "extension"),
                dst=os.path.join("include", "boost", "di", "extension"),
                keep_path=True,
            )
        copy(
            self,
            "di.hpp",
            src=os.path.join(self.source_folder, "include", "boost"),
            dst=os.path.join("include", "boost"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.defines.append(f"BOOST_DI_CFG_DIAGNOSTICS_LEVEL={self.options.diagnostics_level}")
