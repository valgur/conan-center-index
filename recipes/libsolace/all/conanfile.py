# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class LibsolaceConan(ConanFile):
    name = "libsolace"
    description = "High performance components for mission critical applications"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/abbyssoul/libsolace"
    topics = ("HPC", "High reliability", "P10", "solace", "performance", "c++")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _supported_cppstd(self):
        return ["17", "gnu17", "20", "gnu20"]

    def configure(self):
        compiler_version = Version(self, str(self.settings.compiler.version))

        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("This library is not yet compatible with Windows")
        # Exclude compilers that claims to support C++17 but do not in practice
        if (
            (self.settings.compiler == "gcc" and compiler_version < "7")
            or (self.settings.compiler == "clang" and compiler_version < "5")
            or (self.settings.compiler == "apple-clang" and compiler_version < "9")
        ):
            raise ConanInvalidConfiguration(
                "This library requires C++17 or higher support standard. {} {} is not supported".format(
                    self.settings.compiler, self.settings.compiler.version
                )
            )
        if self.settings.compiler.cppstd and not self.settings.compiler.cppstd in self._supported_cppstd:
            raise ConanInvalidConfiguration(
                "This library requires c++17 standard or higher. {} required".format(
                    self.settings.compiler.cppstd
                )
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PKG_CONFIG"] = "OFF"
        tc.variables["SOLACE_GTEST_SUPPORT"] = "OFF"
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )

    def package_info(self):
        self.cpp_info.libs = ["solace"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("m")
