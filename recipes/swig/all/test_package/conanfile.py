from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
from conan.tools.microsoft import is_msvc


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @property
    def _can_build(self):
        # FIXME: Python does not distribute debug libraries (use cci CPython recipe)
        return not (is_msvc(self) and self.settings.build_type == "Debug")

    def build(self):
        if can_run(self):
            self.run("swig -swiglib")
            if self._can_build:
                cmake = CMake(self)
                cmake.verbose = True
                cmake.configure()
                cmake.build()

    def test(self):
        if can_run(self):
            if self._can_build:
                cmake = CMake(self)
                cmake.test(output_on_failure=True)
            self.run("swig -version")
