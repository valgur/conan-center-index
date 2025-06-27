import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CppADCodeGenConan(ConanFile):
    name = "cppadcodegen"
    description = "Source Code Generation for Automatic Differentiation using Operator Overloading"
    license = "EPL-1.0 AND GPL-3.0-only"
    homepage = "https://github.com/joaoleal/CppADCodeGen"
    topics = ("automatic-differentiation", "code-generation", "autodiff", "codegen", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cppad/[>=20240000.4]")
        self.requires("eigen/3.4.0")
        self.requires("openmp/system")
        # self.requires("adolc/[^2.7.2]")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_ADOLC"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_LLVM"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_Clang"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_LATEX"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("cppad", "cmake_file_name", "CppAD")
        deps.set_property("adolc", "cmake_file_name", "ADOLC")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "epl-v10.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "gpl3.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "cppadcg")
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl"]
