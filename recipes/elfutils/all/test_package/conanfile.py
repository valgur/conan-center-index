import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self):
            return
        self.run("eu-ar --version", env="conanrun")

        bin_path = os.path.join(self.cpp.build.bindir, "test_package")
        archive_path = "archive.a"

        self.run(bin_path, env="conanrun")
        self.run(f"eu-ar r {archive_path} {bin_path}", env="conanrun")
        self.run(f"eu-objdump -d {bin_path}", env="conanrun")
        self.run(f"{bin_path} {bin_path}", env="conanrun")
        self.run(f"{bin_path} {archive_path}", env="conanrun")
