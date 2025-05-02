import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    @property
    def _have_introspection_data(self):
        return str(self.dependencies["gobject-introspection"].options.build_introspection_data) == "True"

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        self.run("g-ir-compiler --version")
        self.run("g-ir-generate --version")
        if self._have_introspection_data:
            self.run("g-ir-inspect fontconfig --print-shlibs --print-typelibs", env=["conanbuild", "conanrun"])
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_basic")
            self.run(bin_path, env="conanrun")
