import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        if can_run(self) and "llvm-core" in self.dependencies:
            bc_file = os.path.join(self.dependencies["libclc"].package_folder, "share", "clc", "nvptx64--.bc")
            self.run(f"llvm-bcanalyzer --disable-histogram {bc_file}", env="conanrun")
