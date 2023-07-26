import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            mpiexec = os.path.join(os.environ["MPI_BIN"], "mpiexec")
            test_package_dir = os.path.join("bin", "test_package")
            command = f"{mpiexec} -mca plm_rsh_agent yes -np 2 {test_package_dir}"
            self.run(command, env="conanrun")
