import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        # self.dependencies["ua-nodeset"] does not work for some reason
        res_dir = list(self.dependencies.values())[0].cpp_info.resdirs[0]
        bin_path = os.path.join(res_dir, "PLCopen")
        assert os.path.exists(bin_path)
