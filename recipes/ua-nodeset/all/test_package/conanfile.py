import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        bin_path = os.path.join(self.deps_user_info["ua-nodeset"].nodeset_dir, "PLCopen")
        assert os.path.exists(bin_path)
