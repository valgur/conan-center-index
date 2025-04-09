import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1.0"


class XpropertyConan(ConanFile):
    name = "xproperty"
    description = "Traitlets-like C++ properties and implementation of the observer pattern."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/jupyter-xeus/xproperty"
    topics = ("observer", "traitlets", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return "14" if Version(self.version) <= "0.12.0" else "17"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if Version(self.version) < "0.12.0":
            self.requires("xtl/0.7.4", transitive_headers=True, transitive_libs=True)
        else:
            self.requires("nlohmann_json/3.11.3")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "xproperty")
        self.cpp_info.set_property("cmake_target_name", "xproperty")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
