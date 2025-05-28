import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)
        version = self.tested_reference_str.split("#")[0].split("/")[1]
        self.requires(f"vulkan-loader/{version}")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

            expected_layers = [
                "VK_LAYER_KHRONOS_profiles",
            ]
            # os.environ["VK_LOADER_DEBUG"] = "all"
            check_layers = os.path.join(self.cpp.build.bindir, "check_vulkan_layers")
            self.run(f"{check_layers} {' '.join(expected_layers)}", env="conanrun")
