import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PartioConan(ConanFile):
    name = "partio"
    description = "Library for easily reading/writing/manipulating common animation particle formats such as PDB, BGEO, PTC."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/wdas/partio"
    topics = ("animation", "point-cloud", "particles", "houdini")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("freeglut/[^3.4.0]")
        self.requires("opengl/system")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "src/doc/CMakeLists.txt", "")
        save(self, "src/py/CMakeLists.txt", "")
        replace_in_file(self, "CMakeLists.txt", 'set(CMAKE_CXX_STANDARD "${WDAS_CXX_STANDARD}")', "")
        replace_in_file(self, "CMakeLists.txt", "find_package(Python REQUIRED COMPONENTS Interpreter Development)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PARTIO_BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["WDAS_CXX_STANDARD"] = ""
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
        rmdir(self, os.path.join(self.package_folder, "lib", "python."))

    def package_info(self):
        self.cpp_info.libs = ["partio"]
        if self.settings.os in ["FreeBSD", "Linux"]:
            self.cpp_info.system_libs = ["m"]
