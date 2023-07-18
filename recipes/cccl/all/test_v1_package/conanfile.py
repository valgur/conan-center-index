from conans import ConanFile, tools
from conan.tools.microsoft import is_msvc
import os


class CcclTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def build(self):
        environment = {}
        if is_msvc(self):
            environment.update(tools.vcvars_dict(self.settings))
            #for k in environment.keys():
                #self.output.highlight(k)
                #self.output.highlight(environment[k])
        with tools.environment_append(environment):
            cxxTest = tools.get_env("CXX")
            #cxxB = self.buildenv_info.vars["CXX"]
            self.output.highlight(f"tools.get_env(\"CXX\") = {cxxTest}")
            #self.output.highlight(f"self.buildenv_info.vars[\"CXX\"] = {cxxB}")
            cxx = "sh cccl "
            self.run("{cxx} {src} -o example".format(
                cxx=cxx, src=os.path.join(self.source_folder, "example.cpp")), win_bash=self.settings.os is "Windows", run_environment=True)

    def test(self):
        if not tools.cross_building(self):
            self.run(os.path.join(self.build_folder, "example"))
