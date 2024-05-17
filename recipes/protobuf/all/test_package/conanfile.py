from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
from conan.tools.env import VirtualRunEnv
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualBuildEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        # note `run=True` so that the runenv can find protoc
        self.requires(self.tested_reference_str, run=True)

    def generate(self):
        venv = VirtualRunEnv(self)
        venv.generate(scope="build")
        venv.generate(scope="run")

        tc = CMakeToolchain(self)
        tc.variables["protobuf_LITE"] = self.dependencies[self.tested_reference_str].options.lite
        tc.cache_variables["CMAKE_PROJECT_test_package_INCLUDE"] = os.path.join(self.source_folder, "macos_make_override.cmake")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
