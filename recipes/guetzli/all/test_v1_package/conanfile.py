import os

from conans import ConanFile, tools


class GoogleguetzliTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    def test(self):
        bees_path = os.path.join(self.source_folder, "bees.png")
        if not tools.cross_building(self.settings):
            app = "guetzli"
            if self.settings.os == "Windows":
                app += ".exe"
            self.run(f"{app} --quality 84 {bees_path} ../test_package/bees.jpg", run_environment=True)
