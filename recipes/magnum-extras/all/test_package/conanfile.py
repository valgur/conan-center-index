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
        if self.options["magnum-extras"].ui:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        if can_run(self):
            executable_ext = ".exe" if self.settings.os == "Windows" else ""
            if self.options["magnum-extras"].player:
                assert os.path.exists(
                    os.path.join(
                        self.dependencies["magnum-extras"].package_folder,
                        "bin",
                        "magnum-player{}".format(executable_ext),
                    )
                )
                # (Cannot run in headless mode) self.run("magnum-player --help")
            if self.options["magnum-extras"].ui_gallery:
                assert os.path.exists(
                    os.path.join(
                        self.dependencies["magnum-extras"].package_folder,
                        "bin",
                        "magnum-ui-gallery{}".format(executable_ext),
                    )
                )
                # (Cannot run in headless mode) self.run("magnum-ui-gallery --help")
            if self.options["magnum-extras"].ui:
                bin_path = os.path.join(self.cpp.build.bindir, "test_package")
                self.run(bin_path, env="conanrun")
