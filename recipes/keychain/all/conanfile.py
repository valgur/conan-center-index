# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get
from conan.tools.gnu import PkgConfigDeps

required_conan_version = ">=1.53.0"


class KeychainConan(ConanFile):
    name = "keychain"
    description = "A cross-platform wrapper for the operating system's credential storage"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/hrantzsch/keychain"
    topics = ("security", "credentials", "password", "cpp11")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [False, True],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("libsecret/0.20.4")

    def build_requirements(self):
        if self.settings.os == "Linux":
            self.build_requires("pkgconf/1.7.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(self.name + "-" + self.version, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()
        tc = PkgConfigDeps(self)
        tc.generate()

    def build(self):
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
        self.cpp_info.libs = collect_libs(self)

        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["Security", "CoreFoundation"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["crypt32"]
