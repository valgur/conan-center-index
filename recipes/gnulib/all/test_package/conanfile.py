import contextlib
import os
import shutil

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout
from conan.tools.files import copy


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        copy(self, "configure.ac", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "Makefile.am", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "test_package.c", src=self.recipe_folder, dst=self.export_sources_folder)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.tool_requires("msys2/cci.latest")
        self.tool_requires("automake/1.16.4")

    def layout(self):
        cmake_layout(self)

    @contextlib.contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self):
                env = {
                    "AR": "{} lib".format(
                        unix_path(self, os.path.join(self.build_folder, "build-aux", "ar-lib"))
                    ),
                    "CC": "cl -nologo",
                    "CXX": "cl -nologo",
                    "LD": "link -nologo",
                    "NM": "dumpbin -symbols",
                    "OBJDUMP": ":",
                    "RANLIB": ":",
                    "STRIP": ":",
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def build(self):
        for src in self.exports_sources:
            shutil.copy(os.path.join(self.source_folder, src), dst=os.path.join(self.build_folder, src))
        with chdir(self.build_folder):
            for fn in ("COPYING", "NEWS", "INSTALL", "README", "AUTHORS", "ChangeLog"):
                save(self, fn, "\n")
            with run_environment(self):
                self.run("gnulib-tool --list", win_bash=tools.os_info.is_windows, run_environment=True)
                self.run(
                    "gnulib-tool --import getopt-posix",
                    win_bash=tools.os_info.is_windows,
                    run_environment=True,
                )
            # m4 built with Visual Studio does not support executing *nix utils (e.g. `test`)
            with environment_append(self, {"M4": None}) if self.settings.os == "Windows" else no_op(self):
                self.run(
                    "{} -fiv".format(os.environ["AUTORECONF"]),
                    win_bash=tools.os_info.is_windows,
                    run_environment=True,
                )

            with self._build_context():
                autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                autotools.configure()
                autotools.make()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
