import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class InjaConan(ConanFile):
    name = "inja"
    license = "MIT"
    homepage = "https://github.com/pantor/inja"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Inja is a template engine for modern C++, loosely inspired by jinja for python"
    topics = ("jinja2", "string templates", "templates engine")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 11 if Version(self.version) < "3.4.0" else 17

    @property
    def _compilers_minimum_version(self):
        if self._min_cppstd == 11:
            return {}
        return {
            "msvc": "191",
            "gcc": "7",
            "clang": "7",
            "apple-clang": "10",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("nlohmann_json/3.11.3")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
        )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "inja")
        self.cpp_info.set_property("cmake_target_name", "pantor::inja")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
