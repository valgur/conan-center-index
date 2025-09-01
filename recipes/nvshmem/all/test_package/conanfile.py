import os
from functools import cached_property

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type", "cuda"
    generators = "CMakeToolchain", "CMakeDeps"

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def validate(self):
        self.cuda.validate_settings()

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def generate(self):
        tc = self.cuda.CudaToolchain()
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            self.run(os.path.join(self.cpp.build.bindir, "test_package_static"), env="conanrun")
            self.run(os.path.join(self.cpp.build.bindir, "test_package_shared"), env="conanrun")
