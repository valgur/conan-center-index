import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @property
    def _have_lib(self):
        return str(self.dependencies["gettext"].options.libintl) == "True"

    @property
    def _have_tools(self):
        return str(self.dependencies["gettext"].options.tools) == "True"

    def build(self):
        if self._have_lib:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        if not can_run(self):
            return

        if self._have_lib:
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env=f"conanrun")

        if self._have_tools:
            for exe in ["gettext", "ngettext", "msgcat", "msgmerge"]:
                self.run(f"{exe} --version", env="conanrun")
