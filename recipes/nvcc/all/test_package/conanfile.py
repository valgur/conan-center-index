import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
from conan.tools.scm import Version


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type", "cuda"
    generators = "CMakeToolchain", "CMakeDeps"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def validate(self):
        self._utils.validate_cuda_settings(self)

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        v = Version(self.tested_reference_str.split("/")[1])
        self.requires(f"cudart/[~{v.major}.{v.minor}]", run=True)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        self.tool_requires("cmake/[>=3.18 <5]")
        self.tool_requires("cuobjdump/[*]")

    def generate(self):
        tc = self._utils.NvccToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        self.run("nvcc --version")
        bin_path = os.path.join(self.cpp.build.bindir, "test_package")
        if can_run(self):
            self.run(bin_path, env="conanrun")
        self.run(f'cuobjdump "{bin_path}"')
