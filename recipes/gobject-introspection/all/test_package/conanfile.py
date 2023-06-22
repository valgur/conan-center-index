import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "PkgConfigDeps", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        if self.settings.os != "Windows":
            with tools.environment_append(
                {
                    "PKG_CONFIG_PATH": ".",
                }
            ):
                pkg_config = tools.PkgConfig("gobject-introspection-1.0")
                for tool in ["g_ir_compiler", "g_ir_generate", "g_ir_scanner"]:
                    self.run("%s --version" % pkg_config.variables[tool], env="conanrun")
                self.run("g-ir-annotation-tool --version", env="conanrun")
                self.run("g-ir-inspect -h", env="conanrun")

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
