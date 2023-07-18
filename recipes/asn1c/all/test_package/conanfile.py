import os

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
from conan.tools.files import copy


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SUPPORT_PATH"] = self.dependencies["asn1c"].buildenv_info.SUPPORT_PATH
        tc.generate()

    def build(self):
        if not cross_building(self):
            copy(self, "MyModule.asn1", src=self.source_folder, dst=self.build_folder)
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
