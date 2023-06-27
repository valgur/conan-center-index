import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)
        if self._with_systemc_example:
            self.requires("systemc/2.3.3")

    def layout(self):
        cmake_layout(self)

    @property
    def _with_systemc_example(self):
        # systemc is not available on Macos
        return self.settings.os != "Macos"

    def build(self):
        if can_run(self):
            cmake = CMake(self)
            tc.variables["BUILD_SYSTEMC"] = self._with_systemc_example
            cmake.configure()
            cmake.build()

    def test(self):
        if can_run(self):
            verilator_path = os.path.join(self.deps_cpp_info["verilator"].rootpath, "bin", "verilator")
            self.run(f"perl {verilator_path} --version", env="conanrun")
            self.run(os.path.join("bin", "blinky"), env="conanrun")
            if self._with_systemc_example:
                self.run(os.path.join("bin", "blinky_sc"), env="conanrun")
