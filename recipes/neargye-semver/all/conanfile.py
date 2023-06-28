# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class NeargyeSemverConan(ConanFile):
    name = "neargye-semver"
    description = "Semantic Versioning for modern C++"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Neargye/semver"
    topics = ("semver", "semantic", "versioning", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def configure(self):
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)

        min_req_cppstd = "17"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, min_req_cppstd)
        else:
            self.output.warning(
                f"{self.name} recipe lacks information about the {compiler} "
                "compiler standard version support."
            )

        minimal_version = {
            "Visual Studio": "16",
            "gcc": "7.3",
            "clang": "6.0",
            "apple-clang": "10.0",
        }
        # Exclude compilers not supported
        if compiler not in minimal_version:
            self.output.info(f"{self.name} requires a compiler that supports at least C++{min_req_cppstd}")
            return
        if compiler_version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                f"{self.name} requires a compiler that supports at least C++{min_req_cppstd}. "
                f"{compiler} {Version(self.settings.compiler.version.value)} is not supported."
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(
            self,
            "*.hpp",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.names["pkg_config"] = "semver"
        self.cpp_info.names["cmake_find_package"] = "semver"
        self.cpp_info.names["cmake_find_package_multi"] = "semver"
