from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self):
            test_env_dir = "test_env"
            tools.mkdir(test_env_dir)
            bin_path = os.path.join("bin", "test_package")
            handler_exe = "crashpad_handler.exe" if self.settings.os == "Windows" else "crashpad_handler"
            handler_bin_path = os.path.join(self.deps_cpp_info["crashpad"].rootpath, "bin", handler_exe)
            self.run("%s %s/db %s" % (bin_path, test_env_dir, handler_bin_path), run_environment=True)
            if self.settings.os == "Windows":
                handler_exe = "crashpad_handler.com"
                handler_bin_path = os.path.join(self.deps_cpp_info["crashpad"].rootpath, "bin", handler_exe)
                self.run("%s %s/db %s" % (bin_path, test_env_dir, handler_bin_path), run_environment=True)
