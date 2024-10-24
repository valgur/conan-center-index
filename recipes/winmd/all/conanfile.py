import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.50.0"


class WinMDConan(ConanFile):
    name = "winmd"
    description = "C++ winmd parser"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/winmd"
    topics = ("native", "C++", "WinRT", "WinMD")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "8",
            "clang": "12",
            "apple-clang": "12",
            "Visual Studio": "15",
            "msvc": "191",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not (fully) support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        path = Path(self.source_folder, "src", "impl", "winmd_reader", "view.h")
        path.write_text("#include <utility>\n" + path.read_text())

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            pattern="*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "src"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if not is_msvc(self):
            # ignore shadowing errors
            self.cpp_info.cxxflags = ['-fpermissive']
