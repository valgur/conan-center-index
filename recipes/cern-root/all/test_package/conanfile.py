from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    @property
    def _minimum_cpp_standard(self):
        return 11

    @property
    def _cmake_cxx_standard(self):
        compileropt = self.settings.compiler.get_safe("cppstd")
        if compileropt:
            return str(compileropt)
        else:
            return "11"

    def configure(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, self._minimum_cpp_standard)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        env_build = RunEnvironment(self)
        with tools.environment_append(env_build.vars):
            cmake = CMake(self)
            cmake.configure(defs={"CMAKE_CXX_STANDARD": self._cmake_cxx_standard})
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
