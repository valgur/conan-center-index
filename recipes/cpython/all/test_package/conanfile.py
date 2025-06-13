import os
from io import StringIO

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.apple import is_apple_os
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import Environment
from conan.tools.gnu import AutotoolsDeps
from conan.tools.microsoft import is_msvc, VCVars
from conan.tools.scm import Version


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        # These tests can break pip-installed CMake, so add it as a tool_requires.
        self.tool_requires("cmake/[>=3.26 <5]")
        self.tool_requires("cpython/<host_version>")

    def layout(self):
        cmake_layout(self)

    @property
    def _python(self):
        return self.dependencies["cpython"].conf_info.get("user.cpython:python", check_type=str)

    def _cpython_option(self, name, default=False):
        return self.dependencies["cpython"].options.get_safe(name, default)

    @property
    def _py_version(self):
        return Version(str(self.dependencies["cpython"].ref.version).split("-")[0])

    @property
    def _test_setuptools(self):
        # TODO Should we still try to test this?
        # https://github.com/python/cpython/pull/101039
        return self._supports_modules and self._py_version < "3.12"

    @property
    def _supports_modules(self):
        return self._cpython_option("shared", True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_MODULE"] = self._supports_modules
        if not can_run(self):
            tc.variables["Python_EXECUTABLE"] = os.path.join(self.dependencies.build["cpython"].package_folder, "bin", "python").replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self._test_setuptools:
            if is_msvc(self):
                VCVars(self).generate()
            # Just for the setuptools build
            AutotoolsDeps(self).generate(scope="build")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

        if self._test_setuptools:
            setup_args = [
                os.path.join(self.source_folder, "setup.py"),
                "build",
                "--build-base", self.build_folder,
                "--build-platlib", os.path.join(self.build_folder, "lib_setuptools"),
                # Bandaid fix: setuptools places temporary files in a subdirectory of the build folder where the
                # entirety of the absolute path up to this folder is appended (with seemingly no way to stop this),
                # essentially doubling the path length. This may run into Windows max path lengths, so we give ourselves
                # a little bit of wiggle room by making this directory name as short as possible. One of the directory
                # names goes from (for example) "temp.win-amd64-3.10-pydebug" to "t", saving us roughly 25 characters.
                "--build-temp", "t",
            ]
            if self.settings.build_type == "Debug":
                setup_args.append("--debug")
            args = " ".join(f'"{a}"' for a in setup_args)

            env = Environment()
            env.define("DISTUTILS_USE_SDK", "1")
            env.define("MSSdk", "1")
            with env.vars(self).apply():
                self.run(f"{self._python} {args}")

    def _test_module(self, module, should_work):
        try:
            self.run(f'{self._python} "{self.source_folder}/test_package.py" -b "{self.build_folder}" -t {module}', env="conanrun")
        except ConanException:
            if should_work:
                self.output.warning(f"Module '{module}' does not work, but should have worked")
                raise
            self.output.info("Module failed as expected")
            return
        if not should_work:
            raise ConanException(f"Module '{module}' works, but should not have worked")
        self.output.info("Module worked as expected")

    def test(self):
        if not is_msvc(self):
            self.run("python3-config --prefix", env="conanbuild")

        if can_run(self):
            self.run(f"{self._python} --version", env="conanrun")

            self.run(f'{self._python} -c "print(\'hello world\')"', env="conanrun")

            buffer = StringIO()
            self.run(f'{self._python} -c "import sys; print(\'.\'.join(str(s) for s in sys.version_info[:3]))"', buffer, env="conanrun")
            self.output.info(buffer.getvalue())
            version_detected = buffer.getvalue().splitlines()[-1].strip()
            if self._py_version != version_detected:
                raise ConanException(f"python reported wrong version. Expected {self._py_version}. Got {version_detected}.")

            if self._supports_modules:
                self._test_module("gdbm", self._cpython_option("with_gdbm"))
                self._test_module("bz2", self._cpython_option("with_bz2"))
                self._test_module("lzma", self._cpython_option("with_lzma"))
                self._test_module("zstd", self._cpython_option("with_zstd"))
                self._test_module("tkinter", self._cpython_option("with_tkinter"))
                env = Environment()
                env.define("TERM", "ansi")
                with env.vars(self).apply():
                    self._test_module("curses", self._cpython_option("with_curses"))
                self._test_module("expat", True)
                self._test_module("sqlite3", self._cpython_option("with_sqlite3"))
                self._test_module("decimal", True)
                self._test_module("ctypes", True)
                self._test_module("readline", self._cpython_option("with_readline"))
                env = Environment()
                if self.settings.os != "Windows":
                    env.define_path("OPENSSL_CONF", os.path.join(os.sep, "dev", "null"))
                with env.vars(self).apply():
                    self._test_module("ssl", True)

            if is_apple_os(self) and not self._cpython_option("shared"):
                self.output.info(
                    "Not testing the module, because these seem not to work on apple when cpython is built as"
                    " a static library"
                )
                # FIXME: find out why cpython on apple does not allow to use modules linked against a static python
            else:
                if self._supports_modules:
                    env = Environment()
                    env.define_path("PYTHONPATH", os.path.join(self.build_folder, self.cpp.build.libdirs[0]))
                    self.output.info("Testing module (spam) using cmake built module")
                    with env.vars(self).apply():
                        self._test_module("spam", True)

                    if self._test_setuptools:
                        env.define_path("PYTHONPATH", os.path.join(self.build_folder, "lib_setuptools"))
                        self.output.info("Testing module (spam) using setup.py built module")
                        with env.vars(self).apply():
                            self._test_module("spam", True)

            # MSVC builds need PYTHONHOME set. Linux and Mac don't require it to be set if tested after building,
            # but if the package is relocated then it needs to be set.
            env = Environment()
            env.define_path("PYTHONHOME", self.dependencies["cpython"].conf_info.get("user.cpython:pythonhome", check_type=str))
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            with env.vars(self).apply():
                self.run(bin_path, env="conanrun")
