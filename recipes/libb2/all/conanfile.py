# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get

required_conan_version = ">=1.53.0"


class libb2Conan(ConanFile):
    name = "libb2"
    description = (
        "libb2 is a library that implemets the BLAKE2 cryptographic hash function, which is faster than MD5, "
        "SHA-1, SHA-2, and SHA-3, yet is at least as secure as the latest standard SHA-3"
    )
    license = ["CC0-1.0", "OpenSSL", "APSL-2.0"]
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/BLAKE2/BLAKE2"
    topics = ("blake2", "hash")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_sse": [True, False],
        "use_neon": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_sse": False,
        "use_neon": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.use_neon and not "arm" in self.settings.arch:
            raise ConanInvalidConfiguration("Neon sources only supported on arm-based CPUs")
        if self.options.use_neon and self.options.use_sse:
            raise ConanInvalidConfiguration("Neon and SSE can not be used together.")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_SSE"] = self.options.use_sse
        tc.variables["USE_NEON"] = self.options.use_neon
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.source_path.parent)
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs = ["include", os.path.join("include", "libb2")]
