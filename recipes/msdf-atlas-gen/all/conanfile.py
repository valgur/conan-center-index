# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain
from conan.tools.files import copy, get, replace_in_file, save

required_conan_version = ">=1.53.0"


class MsdfAtlasGenConan(ConanFile):
    name = "msdf-atlas-gen"
    description = "MSDF font atlas generator"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Chlumsky/msdf-atlas-gen"
    topics = ("msdf", "font", "atlas")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def layout(self):
        pass

    def requirements(self):
        self.requires("artery-font-format/1.0")
        self.requires("msdfgen/1.9.1")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MSDF_ATLAS_GEN_BUILD_STANDALONE"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(self, cmakelists, "add_subdirectory(msdfgen)", "")
        save(self, cmakelists, "install(TARGETS msdf-atlas-gen-standalone DESTINATION bin)", append=Tru)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libdirs = []

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
