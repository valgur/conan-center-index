import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class XoshiroCppConan(ConanFile):
    name = "xoshiro-cpp"
    description = "Header-only Xoshiro/Xoroshiro PRNG wrapper library for modern C++ (C++17/C++20)"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Reputeless/Xoshiro-cpp"
    topics = ("prng", "xoshiro", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return "17"

    @property
    def _minimum_compilers_version(self):
        return {
            "apple-clang": "10",
            "clang": "6",
            "gcc": "7",
            "Visual Studio": "16",
            "msvc": "192",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.get_safe("compiler.cppstd"):
            check_min_cppstd(self, self._min_cppstd)

        minimum_version = self._minimum_compilers_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "*.hpp",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "include", "xoshiro-cpp"))
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
