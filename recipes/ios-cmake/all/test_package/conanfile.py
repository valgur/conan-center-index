import os

from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        if self.settings.os == "iOS":
            cmake_prog = os.environ.get("CONAN_CMAKE_PROGRAM")
            toolchain = os.environ.get("CONAN_CMAKE_TOOLCHAIN_FILE")
            assert os.path.basename(cmake_prog) == "cmake-wrapper"
            assert os.path.basename(toolchain) == "ios.toolchain.cmake"
