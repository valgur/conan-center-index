import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "gcc"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        basic_layout(self)

    def build(self):
        source_file = os.path.join(self.source_folder, "main.cpp")
        self.run(f"gcc.exe {source_file} @conanbuildinfo.gcc -lstdc++ -o main")

    def test(self):
        if can_run(self):
            self.run("gcc.exe --version")
            self.run("main")
