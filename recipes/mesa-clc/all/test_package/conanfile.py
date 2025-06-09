from conan import ConanFile
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        self.run("mesa_clc --help")
        self.run("vtn_bindgen2", ignore_errors=True)
