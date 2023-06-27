# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import (
    check_min_cppstd,
)
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get

required_conan_version = ">=1.53.0"


class sqlpp11Conan(ConanFile):
    name = "sqlpp11-connector-sqlite3"
    description = "A C++ wrapper for sqlite3 meant to be used in combination with sqlpp11."
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/rbock/sqlpp11-connector-sqlite3"
    topics = ("sqlite3", "sqlpp11", "sql", "database")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_sqlcipher": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_sqlcipher": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("sqlpp11/0.59")
        if self.options.with_sqlcipher:
            self.requires("sqlcipher/4.4.0")
        else:
            self.requires("sqlite3/3.32.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_TESTS"] = False
        tc.variables["SQLCIPHER"] = self.options.with_sqlcipher
        tc.variables["SQLPP11_INCLUDE_DIR"] = self.dependencies["sqlpp11"].cpp_info.includedirs[0]
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["sqlpp11-connector-sqlite3"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m"]
        if self.options.with_sqlcipher:
            self.cpp_info.defines = ["SQLPP_USE_SQLCIPHER"]
