from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "PkgConfigDeps", "CMakeToolchain", "VirtualRunEnv"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            example = os.path.join(self.cpp.build.bindir, "example")
            self.run(example, env="conanrun")
