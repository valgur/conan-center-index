import os

from conan import ConanFile
from conan.tools.cmake import cmake_layout
from conan.tools.files import *


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def test(self):
        bear = self.dependencies.build["bear"].conf_info.get("user.bear:command")
        self.run(f"{bear} -- cc {self.source_folder}/test.c -o test")
        compile_commands = os.path.join(self.build_folder, "compile_commands.json")
        assert os.path.isfile(compile_commands), "compile_commands.json not found"
        self.output.info(f"Generated compile_commands.json:\n{load(self, compile_commands)}")
