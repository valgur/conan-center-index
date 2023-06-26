# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class LogrConan(ConanFile):
    name = "logr"
    description = "Logger frontend substitution for spdlog, glog, etc for server/desktop applications"
    license = "BSD 3-Clause License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ngrodzitski/logr"
    topics = ("logger", "development", "util", "utils", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "backend": ["spdlog", "glog", "log4cplus", "log4cplus-unicode", None],
    }
    default_options = {
        "backend": "spdlog",
    }
    no_copy_source = True

    def configure(self):
        minimal_cpp_standard = "17"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)
        minimal_version = {
            "gcc": "7",
            "clang": "7",
            "apple-clang": "10",
            "Visual Studio": "16",
        }
        compiler = str(self.settings.compiler)
        if compiler not in minimal_version:
            self.output.warn(
                f"{self.name} recipe lacks information about the {compiler} compiler standard version support"
            )
            self.output.warn(
                f"{self.name} requires a compiler that supports at least C++{minimal_cpp_standard}"
            )
            return

        version = Version(self.settings.compiler.version)
        if version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                f"{self.name} requires a compiler that supports at least C++{minimal_cpp_standard}"
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/7.1.2")

        if self.options.backend == "spdlog":
            self.requires("spdlog/1.8.0")
        elif self.options.backend == "glog":
            self.requires("glog/0.4.0")
        elif self.options.backend == "log4cplus":
            self.requires("log4cplus/2.0.5")
        elif self.options.backend == "log4cplus-unicode":
            self.requires("log4cplus/2.0.5")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LOGR_WITH_SPDLOG_BACKEND"] = self.options.backend == "spdlog"
        tc.variables["LOGR_WITH_GLOG_BACKEND"] = self.options.backend == "glog"
        tc.variables["LOGR_WITH_LOG4CPLUS_BACKEND"] = self.options.backend in [
            "log4cplus",
            "log4cplus-unicode",
        ]

        tc.variables["LOGR_INSTALL"] = True

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        if self.options.backend == "log4cplus" and self.options["log4cplus"].unicode:
            raise ConanInvalidConfiguration("backend='log4cplus' requires log4cplus:unicode=False")
        elif self.options.backend == "log4cplus-unicode" and not self.options["log4cplus"].unicode:
            raise ConanInvalidConfiguration("backend='log4cplus-unicode' requires log4cplus:unicode=True")

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
