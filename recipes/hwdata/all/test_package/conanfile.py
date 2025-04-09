import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        resdir = self.dependencies["hwdata"].cpp_info.resdirs[0]
        assert os.path.isfile(os.path.join(resdir, "hwdata", "usb.ids"))
