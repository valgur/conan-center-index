import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps"

    @property
    def _python_executable(self):
        return self.conf.get("user.cpython:python", check_type=str)

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        if not self._python_executable:
            self.tool_requires("cpython/[^3]")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            if self.dependencies["coal"].options.python_bindings:
                self.run(f'"{self._python_executable}" -c "import coal; print(coal.__file__)"', env="conanrun")
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
