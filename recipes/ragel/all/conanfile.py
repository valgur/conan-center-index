from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rmdir
from conan.tools.layout import basic_layout
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os

required_conan_version = ">=2.1"

class RagelConan(ConanFile):
    name = "ragel"
    description = "Ragel compiles executable finite state machines from regular languages"
    license = "GPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.colm.net/open-source/ragel"
    topics = ("FSM", "regex", "fsm-compiler")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "config.h", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        if self.settings.os == "Windows":
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if self.settings.os == "Windows":
            tc = CMakeToolchain(self)
            tc.variables["RAGEL_SOURCE_DIR"] = self.source_folder.replace("\\", "/")
            tc.generate()

            dpes = CMakeDeps(self)
            dpes.generate()
        else:
            env = VirtualBuildEnv(self)
            env.generate()
            if not cross_building(self):
                env = VirtualRunEnv(self)
                env.generate(scope="build")
            tc = AutotoolsToolchain(self)
            tc.generate()

            deps = AutotoolsDeps(self)
            deps.generate()

    def build(self):

        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
            cmake.build()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, pattern="CREDITS", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.install()
        else:
            autotools = Autotools(self)
            autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.runenv_info.define_path("RAGEL_ROOT", self.package_folder)
        self.buildenv_info.define_path("RAGEL_ROOT", self.package_folder)
