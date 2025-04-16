from io import StringIO

from conan import ConanFile
from conan.tools.env import Environment
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    @property
    def _secret_value(self):
        return "SECRET_CONAN_PKG_VARIABLE"

    def generate(self):
        env = Environment()
        env.define("PKG_CONFIG_PATH", self._secret_value)
        envvars = env.vars(self)
        envvars.save_script("conanbuildenv_pkg_config_path")

    def build(self):
        pass # nothing to do, skip hook warning

    def test(self):
        self.run('bash.exe -c ^"make --version^"')
        self.run('bash.exe -c ^"! test -f /bin/link^"')
        self.run('bash.exe -c ^"! test -f /usr/bin/link^"')

        output = StringIO()
        self.run('bash.exe -c "echo $PKG_CONFIG_PATH"', output)
        assert self._secret_value in output.getvalue()
