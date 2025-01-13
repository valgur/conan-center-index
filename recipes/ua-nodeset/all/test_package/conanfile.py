import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        nodeset_dir = self.dependencies["ua-nodeset"].conf_info.get("user.ua-nodeset:nodeset_dir")
        test_path = os.path.join(nodeset_dir, "PLCopen")
        assert os.path.exists(test_path)
