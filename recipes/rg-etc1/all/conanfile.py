# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get, save

required_conan_version = ">=1.53.0"


class RgEtc1Conan(ConanFile):
    name = "rg-etc1"
    description = "A performant, easy to use, and high quality 4x4 pixel block packer/unpacker for the ETC1."
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/richgel999/rg-etc1"
    topics = ("etc1", "packer", "unpacker")

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

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.source_path.parent)
        cmake.build()

    def _extract_license(self):
        with open(os.path.join(self.source_folder, "rg_etc1.h")) as f:
            content_lines = f.readlines()
        license_content = []
        for i in range(52, 75):
            license_content.append(content_lines[i][2:-1])
        save(self, "LICENSE", "\n".join(license_content))

    def package(self):
        cmake = CMake(self)
        cmake.install()
        self._extract_license()
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
