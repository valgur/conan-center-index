from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        if cross_building(self):
            self.tool_requires(str(self.requires["flatc"]))

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="flatbuffers")

    def test(self):
        if can_run(self):
            self.run("flatc --version", env="conanrun")
            self.run("flathash fnv1_16 conan", env="conanrun")
