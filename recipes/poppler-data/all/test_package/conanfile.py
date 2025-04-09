import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        if not os.path.isdir(self.conf.get("user.poppler-data:datadir", check_type=str)):
            raise AssertionError("datadir is not a directory")
