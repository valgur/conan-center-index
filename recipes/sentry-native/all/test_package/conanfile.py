from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.files import *
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            test_env_dir = "test_env"
            mkdir(self, test_env_dir)
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            handler_exe = "crashpad_handler.exe" if self.settings.os == "Windows" else "crashpad_handler"
            handler_bin_path = os.path.join(self.dependencies[self.tested_reference_str].cpp_info.bindir, handler_exe)
            self.run(f"{bin_path} {test_env_dir} {handler_bin_path}", env="conanrun")
