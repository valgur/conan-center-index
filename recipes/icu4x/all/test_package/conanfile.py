import os

from conan import ConanFile
from conan.tools.build import can_run, valid_min_cppstd
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    @property
    def _build_cxx(self):
        return valid_min_cppstd(self, 20)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_CXX"] = self._build_cxx
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package_c")
            self.run(bin_path, env="conanrun")
            if self._build_cxx:
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_cpp")
                self.run(bin_path, env="conanrun")
