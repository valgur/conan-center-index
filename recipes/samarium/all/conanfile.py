from os import path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain, CMakeDeps
from conan.tools.files import copy, get, export_conandata_patches, apply_conandata_patches
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class SamariumConan(ConanFile):
    name = "samarium"
    description = "2-D physics simulation library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://strangequark1041.github.io/samarium/"
    topics = ("cpp20", "physics", "2d", "simulation")

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

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "11.0",
            "Visual Studio": "16",
            "clang": "13",
            "apple-clang": "13",
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
        self.requires("fmt/9.0.0")
        self.requires("sfml/2.5.1")
        self.requires("range-v3/0.12.0")
        self.requires("stb/cci.20210910")
        self.requires("tl-expected/20190710")

    def validate(self):
        if self.version == "1.0.0" and self.settings.os == "Macos":
            raise ConanInvalidConfiguration("Macos not supported for v1.0.0")

        compiler = str(self.settings.compiler)
        if compiler not in self._compilers_minimum_version:
            self.output.warn("Unknown compiler, assuming it supports at least C++20")
            return

        version = Version(self.settings.compiler.version)
        if version < self._compilers_minimum_version[compiler]:
            raise ConanInvalidConfiguration(f"{self.name} requires a compiler that supports at least C++20")

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder="src")
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE.md",
            src=self.folders.source_folder,
            dst=path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["samarium"]
