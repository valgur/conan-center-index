from conan import ConanFile
from conan.tools.build import cross_building

class TestPackageConan(ConanFile):
    settings = "os", "arch", "build_type", "compiler"
    generators = "VirtualBuildEnv"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        if not cross_building(self):
            self.run("mold -v")
