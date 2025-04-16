import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        save(self, "file.txt", "some text")
        assert not os.path.isdir("destionation")
        self.run("nsinstall -D destination")
        assert os.path.isdir("destination")
        assert not os.path.isfile(os.path.join("destination", "file.txt"))
        self.run("nsinstall -t -m 644 file.txt destination")
        assert os.path.isfile(os.path.join("destination", "file.txt"))
