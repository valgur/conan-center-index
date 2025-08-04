import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        # pcc is only able to find share/pmix/pmixcc-wrapper-data.txt when built as shared
        if self.dependencies["openpmix"].options.shared:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        self.run("prte-info")
        if can_run(self) and self.dependencies["openpmix"].options.shared:
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
