from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout
import os

from conan.tools.microsoft import is_msvc


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package_cxx")
            self.run(bin_path, env="conanrun")
            if not is_msvc(self):
                # lerc_computeCompressedSize() fails with a stack overflow on MSVC for some reason
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_c")
                self.run(bin_path, env="conanrun")
