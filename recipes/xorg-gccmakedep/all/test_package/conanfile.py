import os

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.files import copy, load
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"

    def export_sources(self):
        copy(self, "Makefile", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "test_package.c", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "test_package.h", src=self.recipe_folder, dst=self.export_sources_folder)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        basic_layout(self)

    def build(self):
        for src in self.exports_sources:
            copy(self, src, self.source_folder, self.build_folder)

        src = os.path.join(self.build_folder, "test_package.c")
        self.run(f"gccmakedep {src}", env="conanbuild")

        if load(self, os.path.join(self.source_folder, "Makefile")) == os.path.join(
            self.build_folder, "Makefile"
        ):
            raise ConanException("xorg-gccmakedep did not modify `Makefile'")

    def test(self):
        pass
