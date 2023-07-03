from conans import ConanFile, CMake, tools
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "cmake", "cmake_find_package_multi"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self):
            cnf_file = os.path.join(self.source_folder, os.pardir, "test_package", "graph.cnf")
            self.run(f"bliss {cnf_file}", run_environment=True)
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)
