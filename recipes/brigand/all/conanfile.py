import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class BrigandConan(ConanFile):
    name = "brigand"
    description = "A light-weight, fully functional, instant-compile time meta-programming library."
    license = "BSL-1.0"
    topics = ("meta-programming", "boost", "runtime", "header-only")
    homepage = "https://github.com/edouarda/brigand"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_boost": [True, False],
    }
    default_options = {
        "with_boost": True,
    }

    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_boost:
            self.requires("boost/[^1.71.0]", libs=False)

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp",
             os.path.join(self.source_folder, "include", "brigand"),
             os.path.join(self.package_folder, "include", "brigand"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libbrigand")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.options.with_boost:
            self.cpp_info.requires = ["boost::headers"]
        else:
            self.cpp_info.defines.append("BRIGAND_NO_BOOST_SUPPORT")
