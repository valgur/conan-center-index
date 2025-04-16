import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    @property
    def _full_findx11_test(self):
        # Test full FindX11.cmake compatibility.
        # Adds dependencies that are otherwise not included with xorg/system.
        return False

    def requirements(self):
        self.requires(self.tested_reference_str)
        if self._full_findx11_test:
            self.requires("libxft/2.3.8", transitive_headers=True, transitive_libs=True)
            self.requires("xkbcommon/1.6.0", transitive_headers=True, transitive_libs=True, options={
                "with_wayland": False,
                "with_x11": True
            })

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FULL_TEST"] = self._full_findx11_test
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            cmd = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(cmd, env="conanrun")
