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
        cmake.definitions["WITH_UTILITY"] = self.options["corrade"].with_utility
        if self.deps_cpp_info["corrade"].version == "2019.10":
            cmake.definitions["VERSION_2019_10"] = True
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self):
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)

            if self.options["corrade"].with_utility:
                # Run corrade-rc
                self.run("corrade-rc --help", run_environment=True)

        if self.settings.os == "Emscripten":
            bin_path = os.path.join("bin", "test_package.js")
            self.run(f"node {bin_path}", env="conanrun")
