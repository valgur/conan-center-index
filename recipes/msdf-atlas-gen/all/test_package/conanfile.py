import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    @property
    def _atlas_texture_file(self):
        return os.path.join(self.build_folder, "atlas_texture.png")

    @property
    def _atlas_desc_file(self):
        return os.path.join(self.build_folder, "atlas_desc.json")

    def test(self):
        ttf_path = os.path.join(self.source_folder, "Sacramento-Regular.ttf")
        charset_path = os.path.join(self.source_folder, "uppercase_charset")

        ret_code = self.run(
            f"msdf-atlas-gen -font {ttf_path} -charset {charset_path} -imageout"
            f" {self._atlas_texture_file} -json {self._atlas_desc_file}"
        )

        assert ret_code == 0
        assert os.path.isfile(self._atlas_texture_file)
        assert os.path.isfile(self._atlas_desc_file)
