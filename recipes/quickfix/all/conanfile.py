# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    copy,
    export_conandata_patches,
    get,
    rmdir,
)

required_conan_version = ">=1.53.0"


class QuickfixConan(ConanFile):
    name = "quickfix"
    description = "QuickFIX is a free and open source implementation of the FIX protocol"
    license = "The QuickFIX Software License, Version 1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.quickfixengine.org"
    topics = ("FIX", "Financial Information Exchange", "libraries", "cpp")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssl": [True, False],
        "with_postgres": [True, False],
        "with_mysql": [None, "libmysqlclient"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": False,
        "with_postgres": False,
        "with_mysql": None,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_ssl:
            self.requires("openssl/1.1.1q")

        if self.options.with_postgres:
            self.requires("libpq/14.2")

        if self.options.with_mysql == "libmysqlclient":
            self.requires("libmysqlclient/8.0.29")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("QuickFIX cannot be built as shared lib on Windows")
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            raise ConanInvalidConfiguration(
                "QuickFIX doesn't support ARM compilation"
            )  # See issue: https://github.com/quickfix/quickfix/issues/206

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["HAVE_SSL"] = self.options.with_ssl
        tc.variables["HAVE_POSTGRESQL"] = self.options.with_postgres
        tc.variables["HAVE_MYSQL"] = bool(self.options.with_mysql)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="quickfix")

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "config.h", dst=os.path.join("include", "quickfix"), src=self.build_folder)
        copy(
            self,
            "Except.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "src", "C++"),
        )
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

        if self.options.with_ssl:
            self.cpp_info.defines.append("HAVE_SSL=1")

        if self.options.with_postgres:
            self.cpp_info.defines.append("HAVE_POSTGRESQL=1")

        if self.options.with_mysql:
            self.cpp_info.defines.append("HAVE_MYSQL=1")

        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32"])
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "m"])
