"""Conan recipe package for Google FlatBuffers - Flatc
"""
# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.47.0"


class FlatcConan(ConanFile):
    name = "flatc"
    description = "Memory Efficient Serialization Library"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://google.github.io/flatbuffers/"
    topics = ("flatbuffers", "serialization", "rpc", "json-parser", "installer")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    deprecated = "flatbuffers"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"
        if is_msvc(self) and self.options.shared:
            tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["FLATBUFFERS_BUILD_TESTS"] = False
        tc.variables["FLATBUFFERS_BUILD_SHAREDLIB"] = False
        tc.variables["FLATBUFFERS_BUILD_FLATLIB"] = True
        tc.variables["FLATBUFFERS_BUILD_FLATC"] = True
        tc.variables["FLATBUFFERS_BUILD_FLATHASH"] = True

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        extension = ".exe" if self.settings.os == "Windows" else ""
        bin_dir = os.path.join(self.build_folder, "bin")
        copy(self, pattern="flatc" + extension, dst=os.path.join(self.package_folder, "bin"), src=bin_dir)
        copy(self, pattern="flathash" + extension, dst=os.path.join(self.package_folder, "bin"), src=bin_dir)
        copy(
            self,
            pattern="BuildFlatBuffers.cmake",
            dst=os.path.join(self.package_folder, "bin/cmake"),
            src=os.path.join(self.source_folder, "CMake"),
        )

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
        self.cpp_info.builddirs.append("bin/cmake")
        self.cpp_info.build_modules.append("bin/cmake/BuildFlatBuffers.cmake")
