import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GslLiteConan(ConanFile):
    name = "gsl-lite"
    description = "ISO C++ Core Guidelines Library implementation for C++98, C++11 up"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gsl-lite.github.io/gsl-lite/"
    topics = ("GSL", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE",  src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if Version(self.version) >= "1.0.0":
            rmdir(self, os.path.join(self.package_folder, "share"))
        else:
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "gsl-lite")
        self.cpp_info.set_property("cmake_target_name", "gsl::gsl-lite")
        version_major = Version(self.version).major
        self.cpp_info.set_property("cmake_target_aliases", [f"gsl::gsl-lite-v{version_major}"])

        # The official CMake config also defines both gsl::gsl-lite-v0 and gsl::gsl-lite-v1 targets,
        # and adds a -Dgsl_CONFIG_DEFAULTS_VERSION=0 define to the v0 one.
        # Not reproducing this here to not accidentally break recipes
        # that are (implicitly) adding gsl-lite::gsl-lite to self.cpp_info.requires.
        # The user can still add that define manually, if necessary.
