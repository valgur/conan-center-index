import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    @property
    def file_io(self):
        return {
            "c": {
                "compiler": "$CC",
                "src": os.path.join(self.source_folder, "hello.c"),
                "bin": os.path.join(self.build_folder, "hello_c"),
            },
            "cpp": {
                "compiler": "$CXX",
                "src": os.path.join(self.source_folder, "hello.cpp"),
                "bin": os.path.join(self.build_folder, "hello_cpp"),
            },
            "fortran": {
                "compiler": "$FC",
                "src": os.path.join(self.source_folder, "hello.f90"),
                "bin": os.path.join(self.build_folder, "hello_f90"),
            },
        }

    def build(self):
        self.run("echo PATH: $PATH")
        for language, files in self.file_io.items():
            self.output.info(f"Testing build using {language} compiler")
            # Confirm compiler is propagated to env
            envvar = files["compiler"].split("$")[1]
            self.run(f"echo {envvar}: {files['compiler']}", env="conanbuild")
            self.run(f"{files['compiler']} --version", env="conanbuild")
            self.run(f"{files['compiler']} -dumpversion", env="conanbuild")
            # Confirm files can be compiled
            self.run(f"{files['compiler']} {files['src']} -o {files['bin']}", env="conanbuild")
            self.output.info(f"Successfully built {files['bin']}")

    def test(self):
        for language, files in self.file_io.items():
            self.output.info(f"Testing application built using {language} compiler")
            if can_run(self):
                chmod_plus_x(files["bin"])
                if self.settings.os == "Linux":
                    self.run(f"readelf -l {files['bin']}", env="conanrun")
                elif self.settings.os == "Macos":
                    self.run(f"otool -L {files['bin']}", env="conanrun")
                self.run(files["bin"], env="conanrun")


def chmod_plus_x(name):
    if os.name == "posix":
        os.chmod(name, os.stat(name).st_mode | 0o111)
