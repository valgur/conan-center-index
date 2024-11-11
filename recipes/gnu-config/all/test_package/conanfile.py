from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"
    win_bash = True

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        if self.settings_build.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            self.tool_requires("msys2/cci.latest")

    def test(self):
        self.run("config.guess")
        self.run("config.sub --version")
