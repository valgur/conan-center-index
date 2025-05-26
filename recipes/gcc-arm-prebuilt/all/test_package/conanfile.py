import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str, run=True)

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
            if not can_run(self):
                continue
            self.run(f"{files['compiler']} --version", env="conanbuild")
            self.run(f"{files['compiler']} -dumpversion", env="conanbuild")
            # Confirm files can be compiled
            self.run(f"{files['compiler']} {files['src']} -o {files['bin']}", env="conanbuild")
            self.output.info(f"Successfully built {files['bin']}")

    def test(self):
        if not can_run(self):
            return
        for language, files in self.file_io.items():
            self.output.info(f"Testing application built using {language} compiler")
            if self.settings.os == "Linux":
                self.run(f"readelf -l {files['bin']}", env="conanrun")
            elif self.settings.os == "Macos":
                self.run(f"otool -L {files['bin']}", env="conanrun")
