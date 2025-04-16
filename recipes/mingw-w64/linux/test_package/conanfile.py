import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class MinGWTestConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def build(self):
        source_file = os.path.join(self.source_folder, "main.cpp")
        self.run(f"x86_64-w64-mingw32-g++ {source_file} -lstdc++ -o main", env="conanbuild")

    def test(self):
        if can_run(self):
            self.run("x86_64-w64-mingw32-g++ --version", env="conanbuild")
