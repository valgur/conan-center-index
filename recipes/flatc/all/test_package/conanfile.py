from conan.tools.build import can_run
from conans import ConanFile, CMake, tools


class TestPackageConan(ConanFile):
    settings = "os", "arch"
    generators = "cmake", "cmake_find_package"

    def build_requirements(self):
        if tools.cross_building(self.settings):
            self.build_requires(str(self.requires["flatc"]))

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="flatbuffers")

    def test(self):
        if can_run(self):
            self.run("flatc --version", run_environment=True)
            self.run("flathash fnv1_16 conan", run_environment=True)
