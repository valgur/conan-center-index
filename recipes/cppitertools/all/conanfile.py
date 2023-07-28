import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class CppItertoolsConan(ConanFile):
    name = "cppitertools"
    description = "Implementation of python itertools and builtin iteration functions for C++17"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ryanhaining/cppitertools"
    topics = ("cpp17", "iter", "itertools", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "zip_longest": [True, False],
    }
    default_options = {
        "zip_longest": False,
    }
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.zip_longest:
            self.requires("boost/1.82.0")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        minimal_version = {
            "Visual Studio": "15",
            "msvc": "191",
            "gcc": "7",
            "clang": "5.0",
            "apple-clang": "9.1",
        }
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)

        if compiler not in minimal_version:
            self.output.info("{} requires a compiler that supports at least C++17".format(self.name))
            return

        # Exclude compilers not supported by cppitertools
        if compiler_version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                "{} requires a compiler that supports at least C++17. {} {} is not".format(
                    self.name, compiler, Version(self.settings.compiler.version.value)
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            "*.hpp",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "include", "cppitertools"),
            excludes=("examples/**", "test/**"),
        )
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cppitertools")
        self.cpp_info.set_property("cmake_target_name", "cppitertools::cppitertools")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
