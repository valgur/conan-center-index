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
        tc = CMakeToolchain(self)
        tc.variables["WITH_BULLET"] = self.options["magnum-integration"].with_bullet
        tc.variables["WITH_DART"] = self.options["magnum-integration"].with_dart
        tc.variables["WITH_EIGEN"] = self.options["magnum-integration"].with_eigen
        tc.variables["WITH_GLM"] = self.options["magnum-integration"].with_glm
        tc.variables["WITH_IMGUI"] = self.options["magnum-integration"].with_imgui
        tc.variables["WITH_OVR"] = self.options["magnum-integration"].with_ovr
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

        if self.settings.os == "Emscripten":
            bin_path = os.path.join(self.cpp.build.bindir, "test_package.js")
            self.run(f"node {bin_path}", env="conanrun")
