import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def build(self):
        self.run(f"go build -o {self.build_folder}/hello {self.source_folder}/hello.go", cwd=self.source_folder)

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "hello")
            self.run(bin_path, env="conanrun")
