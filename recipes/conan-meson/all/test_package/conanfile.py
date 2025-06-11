import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    python_requires = "conan-meson/latest"

    def layout(self):
        basic_layout(self)

    def test(self):
        fix_libnames = self.python_requires["conan-meson"].module._fix_libnames
        save(self, os.path.join(self.build_folder, "libxyz.a"), "")
        fix_libnames(self, self.build_folder)
        assert os.path.exists(os.path.join(self.build_folder, "xyz.lib"))
