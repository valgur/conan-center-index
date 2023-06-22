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

    @property
    def _extra_flags(self):
        return self.deps_user_info["platform.hashing"].suggested_flags

    def build(self):
        if self.settings.compiler != "Visual Studio":
            if not self._extra_flags:
                raise ConanException(
                    "Suggested flags are not available for os={}/arch={}".format(
                        self.settings.os, self.settings.arch
                    )
                )

        cmake = CMake(self)
        if self.settings.compiler != "Visual Studio":
            tc.variables["EXTRA_FLAGS"] = self._extra_flags
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
