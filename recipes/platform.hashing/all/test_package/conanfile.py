import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
from conan.tools.microsoft import is_msvc
from conans.errors import ConanInvalidConfiguration


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @property
    def _extra_flags(self):
        return self.deps_user_info["platform.hashing"].suggested_flags

    def validate(self):
        if not is_msvc(self):
            if not self._extra_flags:
                raise ConanInvalidConfiguration(
                    f"Suggested flags are not available for os={self.settings.os}/arch={self.settings.arch}"
                )

    def generate(self):
        tc = CMakeToolchain(self)
        if not is_msvc(self):
            tc.variables["EXTRA_FLAGS"] = self._extra_flags
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
