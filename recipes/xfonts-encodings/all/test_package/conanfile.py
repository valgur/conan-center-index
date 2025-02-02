import os

from conan import ConanFile
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        env_vars = self.dependencies[self.tested_reference_str].runenv_info.vars(self)
        fontenc_dir = env_vars["FONT_ENCODINGS_DIRECTORY"]
        self.output.info(f"FONT_ENCODINGS_DIRECTORY: {fontenc_dir}")
        assert os.path.isdir(fontenc_dir)
