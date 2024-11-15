from conan import ConanFile
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        self.tool_requires("cpython/[>=3.12 <3.13]")

    def test(self):
        self.run('python -c "'
                 'import collections; '
                 'output = collections.defaultdict(int); '
                 'from xcbgen import xtypes"',
                 env="conanbuild")
