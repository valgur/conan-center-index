import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibStudXmlConan(ConanFile):
    name = "libstudxml"
    description = "A streaming XML pull parser and streaming XML serializer implementation for modern, standard C++."
    topics = ("xml", "xml-parser", "serialization")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.codesynthesis.com/projects/libstudxml/"
    license = "MIT"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("expat/[>=2.6.2 <3]", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # unvendor expat
        rmdir(self, os.path.join(self.source_folder, "libstudxml", "details", "expat"))
        replace_in_file(self, os.path.join(self.source_folder, "libstudxml", "parser.hxx"),
                        "#ifndef LIBSTUDXML_EXTERNAL_EXPAT",
                        "#if 0")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libstudxml")
        self.cpp_info.libs = ["studxml"]
        self.cpp_info.defines = ["LIBSTUDXML_SHARED" if self.options.shared else "LIBSTUDXML_STATIC"]
