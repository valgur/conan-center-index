import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        bin_path = os.path.join(
            self.dependencies["objectbox-generator"].package_folder, "bin", "objectbox-generator"
        )
        self.run(f"{bin_path} -help")
