from conan import ConanFile
import os

from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        self.run("perl --version")
        perl_script = os.path.join(self.source_folder, "list_files.pl")
        self.run(f"perl {perl_script}")
