import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class STXConan(ConanFile):
    name = "stx"
    description = "C++17 & C++ 20 error-handling and utility extensions."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/lamarrr/STX"
    topics = ("error-handling", "result", "option", "backtrace", "panic")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "backtrace": [True, False],
        "custom_panic_handler": [True, False],
    }
    default_options = {
        "fPIC": True,
        "backtrace": False,
        "custom_panic_handler": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.backtrace:
            self.requires("abseil/[>=20230125.3]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["STX_ENABLE_BACKTRACE"] = self.options.backtrace
        tc.variables["STX_CUSTOM_PANIC_HANDLER"] = self.options.custom_panic_handler
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
        self.cpp_info.libs = ["stx"]

        if self.options.backtrace:
            self.cpp_info.requires = [
                "abseil::absl_stacktrace",
                "abseil::absl_symbolize"
            ]

        if self.settings.os in ["Linux", "FreeBSD", "Android"]:
            self.cpp_info.system_libs = ["atomic"]
