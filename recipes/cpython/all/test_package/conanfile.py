import os
import re
from io import StringIO

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building, can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.env import VirtualRunEnv, VirtualBuildEnv, Environment
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @property
    def _python(self):
        return self.dependencies["cpython"].conf_info.get("user.cpython:python", check_type=str)

    @property
    def _clean_py_version(self):
        return re.match(r"^[0-9.]+", str(self.dependencies["cpython"].ref.version)).group(0)

    @property
    def _py_version(self):
        return Version(self.dependencies["cpython"].ref.version)

    @property
    def _pymalloc(self):
        return bool(self.dependencies["cpython"].options.get_safe("pymalloc", False))

    @property
    def _cmake_try_FindPythonX(self):
        # FIXME: re-enable
        # return not is_msvc(self) or self.settings.build_type != "Debug"
        return False

    @property
    def _supports_modules(self):
        return not is_msvc(self) or self.dependencies["cpython"].options.shared

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_MODULE"] = self._supports_modules
        tc.generate()

        vb = VirtualBuildEnv(self)
        vb.generate()

        if can_run(self):
            env = Environment()
            env.define("DISTUTILS_USE_SDK", "1")
            env.define("MSSdk", "1")

            if self._cpython_option("with_curses"):
                env.define("TERM", "ansi")
            if is_apple_os(self) and not self.dependencies["cpython"].options.shared:
                env.append_path("PYTHONPATH", self.build_folder)
            env_vars = env.vars(self, scope="conanrun")
            env_vars.save_script("modenv")

            vr = VirtualRunEnv(self)
            vr.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _test_module(self, module, should_work):
        try:
            self.run(f"{self._python} {self.source_folder}/test_package.py -b {self.build_folder} -t {module}")
        except ConanException:
            if should_work:
                self.output.warning(f"Module '{module}' does not work, but should have worked")
                raise
            self.output.info("Module failed as expected")
            return
        if not should_work:
            raise ConanException(f"Module '{module}' works, but should not have worked")
        self.output.info("Module worked as expected")

    def _cpython_option(self, name):
        return self.dependencies["cpython"].options.get_safe(name, False)

    def test(self):
        if not cross_building(self, skip_x64_x86=True):
            self.run(f"{self._python} -c \"print('hello world')\"")

            buffer = StringIO()
            self.run(f"{self._python} -c \"import sys; print('.'.join(str(s) for s in sys.version_info[:3]))\"", buffer)
            self.output.info(buffer.getvalue())
            version_detected = buffer.getvalue().splitlines()[-1].strip()
            if self._clean_py_version != version_detected:
                raise ConanException(
                    f"python reported wrong version. Expected {self._clean_py_version}. Got {version_detected}."
                )

            if self._supports_modules:
                self._test_module("gdbm", self._cpython_option("with_gdbm"))
                self._test_module("bz2", self._cpython_option("with_bz2"))
                self._test_module("bsddb", self._cpython_option("with_bsddb"))
                self._test_module("lzma", self._cpython_option("with_lzma"))
                self._test_module("tkinter", self._cpython_option("with_tkinter"))
                os.environ["TERM"] = "ansi"
                self._test_module("curses", self._cpython_option("with_curses"))

                self._test_module("expat", True)
                self._test_module("sqlite3", True)
                self._test_module("decimal", True)
                self._test_module("ctypes", True)

            if is_apple_os(self) and not self.dependencies["cpython"].options.shared:
                self.output.info(
                    "Not testing the module, because these seem not to work on apple when cpython is built as"
                    " a static library"
                )
                # FIXME: find out why cpython on apple does not allow to use modules linked against a static python
            else:
                if self._supports_modules:
                    os.environ["PYTHONPATH"] = os.path.join(self.build_folder, "lib")
                    self.output.info("Testing module (spam) using cmake built module")
                    self._test_module("spam", True)

                    os.environ["PYTHONPATH"] = os.path.join(self.build_folder, "lib_setuptools")
                    self.output.info("Testing module (spam) using setup.py built module")
                    self._test_module("spam", True)

            # MSVC builds need PYTHONHOME set.
            if self.dependencies["cpython"].conf_info.get("user.cpython:module_requires_pythonhome", check_type=bool):
                os.environ["PYTHONHOME"] = self.dependencies["cpython"].conf_info.get("user.cpython:pythonhome", check_type=str)
            self.run(os.path.join(self.cpp.build.bindir, "test_package"), env="conanrun")
