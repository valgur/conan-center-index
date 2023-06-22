from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        tc = CMakeToolchain(self)
        tc.variables["MSGPACK_C_API"] = self.options["msgpack"].c_api
        tc.variables["MSGPACK_CPP_API"] = self.options["msgpack"].cpp_api
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            if self.options["msgpack"].c_api:
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_c")
                self.run(bin_path, env="conanrun")
            if self.options["msgpack"].cpp_api:
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_cpp")
                self.run(bin_path, env="conanrun")
