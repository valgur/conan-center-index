from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        tc = CMakeToolchain(self)
        tc.variables["ROCKSDB_SHARED"] = self.options["rocksdb"].shared
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            if not self.options["rocksdb"].shared:
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_cpp")
                self.run(bin_path, env="conanrun")

            bin_path = os.path.join(self.cpp.build.bindir, "test_package_stable_abi")
            self.run(bin_path, env="conanrun")
