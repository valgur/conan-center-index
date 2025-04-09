import os
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"

class LsQpackConan(ConanFile):
    name = "ls-qpack"
    description = "QPACK compression library for use with HTTP/3"
    license = "MIT",
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/litespeedtech/ls-qpack/"
    topics = ("compression", "quic", "http3", "qpack")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_xxh": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_xxh": True,
    }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_xxh:
            self.requires("xxhash/0.8.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["LSQPACK_TESTS"] = False
        tc.variables["LSQPACK_BIN"] = False
        tc.variables["LSQPACK_XXH"] = self.options.with_xxh
        tc.generate()

        dpes = CMakeDeps(self)
        dpes.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=Path(self.source_folder).parent)
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["ls-qpack"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["m"]
        if self.settings.os == "Windows":
            self.cpp_info.includedirs.append(os.path.join("include", "wincompat"))
