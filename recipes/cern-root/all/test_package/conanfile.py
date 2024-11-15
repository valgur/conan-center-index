from conans import CMake, ConanFile, RunEnvironment, tools
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package"

    def validate(self):
        tools.check_min_cppstd(self, 11)

    def build(self):
        env_build = RunEnvironment(self)
        with tools.environment_append(env_build.vars):
            cmake = CMake(self)
            cmake.configure(
                defs={
                    "CMAKE_CXX_STANDARD": str(self.settings.compiler.cppstd),
                }
            )
            cmake.build()

    def test(self):
        if not tools.cross_building(self):
            self._check_binaries_are_found()
            self._check_root_dictionaries()

    def _check_binaries_are_found(self):
        self.run("root -q", run_environment=True)

    def _check_root_dictionaries(self):
        bin_path = os.path.join("bin", "testrootdictionaries")
        self.run(bin_path, run_environment=True)
