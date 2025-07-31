import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        assert os.path.exists(os.path.join(self.dependencies[self.tested_reference_str].cpp_info.bindir, "gas-preprocessor.pl"))
        if can_run(self) and self.settings_build.os != "Windows":
            self.run("gas-preprocessor.pl -help", env="conanrun")
