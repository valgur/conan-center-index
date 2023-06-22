import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        if hasattr(self, "settings_build"):
            self.tool_requires(str(self.requires["ftjam"]))

    def layout(self):
        cmake_layout(self)

    def build(self):
        for f in ("header.h", "main.c", "source.c", "Jamfile"):
            shutil.copy(os.path.join(self.source_folder, f), os.path.join(self.build_folder, f))
        if not tools.cross_building(self):
            assert os.path.isfile(tools.get_env("JAM"))

            vars = AutoToolsBuildEnvironment(self).vars
            vars["CCFLAGS"] = vars["CFLAGS"]
            vars["C++FLAGS"] = vars["CXXFLAGS"]
            vars["LINKFLAGS"] = vars["LDFLAGS"]
            vars["LINKLIBS"] = vars["LIBS"]
            with tools.environment_append(vars):
                self.run("{} -d7".format(tools.get_env("JAM")), run_environment=True)

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
