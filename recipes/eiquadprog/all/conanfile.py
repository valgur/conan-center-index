import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"

class EiquadprogConan(ConanFile):
    name = "eiquadprog"
    description = (
        "This package contains different C++ implementations of the algorithm of Goldfarb and "
        "Idnani for the solution of a (convex) Quadratic Programming problem by means of a dual method."
    )
    license = ("LGPL-3.0", "GPL-3.0")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/stack-of-tasks/eiquadprog"
    topics = ("algebra", "math", "robotics", "optimization", "quadratic-programming")
    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)

    def validate(self):
        if self.settings.compiler == "msvc":
            raise ConanInvalidConfiguration("MSVC is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "eiquadprog")
        self.cpp_info.set_property("cmake_target_name", "eiquadprog::eiquadprog")
        self.cpp_info.set_property("pkg_config_name", "eiquadprog")
        self.cpp_info.libs = ["eiquadprog"]
