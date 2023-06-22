import os

from conan import ConanFile
from conan.tools.build import can_run, cross_building
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
        if cross_building(self):
            return

        env_build = RunEnvironment(self)
        with tools.environment_append(env_build.vars):
            cmake = CMake(self)
            if tools.os_info.is_macos and self.options["flatcc"].shared:
                # Because of MacOS System Integraty Protection it is currently not possible to run the flatcc
                # executable from cmake if it is linked shared. As a temporary work-around run flatcc here in
                # the build function.
                tools.mkdir(os.path.join(self.build_folder, "generated"))
                self.run(
                    "flatcc -a -o "
                    + os.path.join(self.build_folder, "generated")
                    + " "
                    + os.path.join(self.source_folder, "monster.fbs"),
                    run_environment=True,
                )
                cmake.definitions["MACOS_SIP_WORKAROUND"] = True
            cmake.configure()
            cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.deps_cpp_info["flatcc"].rootpath, "bin", "flatcc")
            if not os.path.isfile(bin_path) or not os.access(bin_path, os.X_OK):
                raise ConanException("flatcc doesn't exist.")
        else:
            bin_path = os.path.join(self.build_folder, "bin", "monster")
            self.run(bin_path, cwd=self.source_folder, env="conanrun")
