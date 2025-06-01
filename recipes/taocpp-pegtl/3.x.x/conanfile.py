import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class TaoCPPPEGTLConan(ConanFile):
    name = "taocpp-pegtl"
    description = "Parsing Expression Grammar Template Library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/taocpp/pegtl"
    topics = ("peg", "header-only", "cpp",
              "parsing", "cpp17", "cpp11", "grammar")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "boost_filesystem": [True, False],
    }
    default_options = {
        "boost_filesystem": False,
    }
    no_copy_source = True

    def configure(self):
        if self.options.boost_filesystem:
            self.options["boost"].with_filesystem = True

    def requirements(self):
        if self.options.boost_filesystem:
            self.requires("boost/[^1.71.0]")

    def validate(self):
        check_min_cppstd(self, 17)

    def package_id(self):
        self.info.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "pegtl")
        self.cpp_info.set_property("cmake_target_name", "taocpp::pegtl")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.options.boost_filesystem:
            self.cpp_info.requires.append("boost::filesystem")
            self.cpp_info.defines.append("TAO_PEGTL_BOOST_FILESYSTEM")
        elif self.settings.compiler == "clang" and "10" <= Version(self.settings.compiler.version) < "12":
            self.cpp_info.defines.append("TAO_PEGTL_STD_EXPERIMENTAL_FILESYSTEM")
