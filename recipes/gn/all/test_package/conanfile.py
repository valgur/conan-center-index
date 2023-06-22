import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("ninja/1.10.2")

    def layout(self):
        cmake_layout(self)

    @contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self.settings):
                yield
        else:
            compiler_defaults = {}
            if self.settings.compiler == "gcc":
                compiler_defaults = {
                    "CC": "gcc",
                    "CXX": "g++",
                    "AR": "ar",
                    "LD": "g++",
                }
            elif self.settings.compiler in ("apple-clang", "clang"):
                compiler_defaults = {
                    "CC": "clang",
                    "CXX": "clang++",
                    "AR": "ar",
                    "LD": "clang++",
                }
            env = {}
            for k in ("CC", "CXX", "AR", "LD"):
                v = get_env(self, k, compiler_defaults.get(k, None))
                if v:
                    env[k] = v
            with environment_append(self, env):
                yield

    @property
    def _target_os(self):
        if is_apple_os(self.settings.os):
            return "mac"
        # Assume gn knows about the os
        return {
            "Windows": "win",
        }.get(str(self.settings.os), str(self.settings.os).lower())

    @property
    def _target_cpu(self):
        return {
            "x86_64": "x64",
        }.get(str(self.settings.arch), str(self.settings.arch))

    def build(self):
        if not cross_building(self.settings):
            with chdir(self.source_folder):
                gn_args = [
                    os.path.relpath(os.path.join(self.build_folder, "bin"), os.getcwd()).replace("\\", "/"),
                    '--args="target_os=\\"{os_}\\" target_cpu=\\"{cpu}\\""'.format(
                        os_=self._target_os, cpu=self._target_cpu
                    ),
                ]
                self.run("gn gen {}".format(" ".join(gn_args)), env="conanrun")
            with self._build_context():
                self.run("ninja -v -j{} -C bin".format(cpu_count(self)), env="conanrun")

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
