from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout
import os


class TzTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        if self.settings_build.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            self.tool_requires("msys2/cci.latest")

    def build(self):
        pass

    def test(self):
        if can_run(self):
            tzdata = self.dependencies["tz"].runenv_info.vars(self).get("TZDATA")
            with_binary_db = str(self.dependencies["tz"].options.with_binary_db)
            if with_binary_db:
                self.output.info("Test that binary tzdb is readable")
                la_tz = os.path.join(tzdata, "America", "Los_Angeles")
                self.run(f"zdump {la_tz}", env="conanrun")
            else:
                self.output.info("Test that source tzdb is readable")
                cmd = "python -c \"import os; tzdata = os.environ['TZDATA']; f=open(os.path.join(tzdata, 'factory'), 'r'); s = f.read(); f.close(); print(s)\""
                self.run(cmd, env="conanrun")
