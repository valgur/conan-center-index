import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class MetallConan(ConanFile):
    name = "metall"
    description = "Meta allocator for persistent memory"
    license = ("MIT", "Apache-2.0")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/LLNL/metall"
    topics = (
        "cpp",
        "allocator",
        "memory-allocator",
        "persistent-memory",
        "ecp",
        "exascale-computing",
        "header-only",
    )

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "8.3",
            "clang": "9",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.79.0")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        if self.settings.os in ["Linux", "FreeBSD"] or is_apple_os(self):
            raise ConanInvalidConfiguration("Metall requires some POSIX functionalities like mmap.")

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.name} {self.version} requires C++17, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(
            self,
            "*",
            src=os.path.join(self.source_folder, "include"),
            dst=os.path.join(self.package_folder, "include"),
        )
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYRIGHT", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Metall")
        self.cpp_info.set_property("cmake_target_name", "Metall::Metall")

        self.cpp_info.names["cmake_find_package"] = "Metall"
        self.cpp_info.names["cmake_find_package_multi"] = "Metall"

        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

        if self.settings.compiler == "gcc" or (
            self.settings.os == "Linux" and self.settings.compiler == "clang"
        ):
            if Version(self.settings.compiler.version) < "9":
                self.cpp_info.system_libs += ["stdc++fs"]

        self.cpp_info.requires = ["boost::headers"]
