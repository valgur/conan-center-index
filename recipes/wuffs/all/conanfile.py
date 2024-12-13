import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class WuffsConan(ConanFile):
    name = "wuffs"
    description = "Wuffs is a memory-safe programming language for Wrangling Untrusted File Formats Safely."
    license = "Apache-2.0 OR MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/wuffs"
    topics = ("programming-language", "parsing", "memory-safety", "codec")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "header_only": False,
    }
    languages = ["C"]
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        if self.info.options.header_only:
            self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _api_version(self):
        version = Version(self.version)
        return f"{version.major}.{version.minor}"

    def generate(self):
        if not self.options.header_only:
            tc = CMakeToolchain(self)
            tc.cache_variables["API_VERSION"] = self._api_version
            tc.generate()

    def build(self):
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.install()
        else:
            copy(self, f"wuffs-v{self._api_version}.c",
                 os.path.join(self.source_folder, "release", "c"),
                 os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libs = ["wuffs"]
