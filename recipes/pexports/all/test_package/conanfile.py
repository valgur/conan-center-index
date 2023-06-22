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
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        if can_run(self):
            self.run("pexports -H")
            if self.settings.os == "Windows":
                bin_path = os.path.join("bin", "test_package")
                self.run(bin_path, run_environment=True)
                exports_def_path = os.path.join(self.build_folder, "exports.def")
                exports_def_contents = load(self, exports_def_path)
                self.output.info("{} contents:\n{}".format(exports_def_path, exports_def_contents))
                if not "test_package_function" in exports_def_contents:
                    raise ConanException("pexport could not detect `test_package_function` in the dll")
