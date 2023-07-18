from conans import ConanFile, tools
from conans.errors import ConanException


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def test(self):
        self.run("config.guess", run_environment=True, win_bash=tools.os_info.is_windows)
        try:
            triplet = tools.get_gnu_triplet(str(self.settings.os), str(self.settings.arch), str(self.settings.compiler))
            self.run(f"config.sub {triplet}", run_environment=True, win_bash=tools.os_info.is_windows)
        except ConanException:
            self.output.info("Current configuration is not supported by GNU config.\nIgnoring...")
