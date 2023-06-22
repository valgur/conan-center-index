import os
import shutil

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout
from conan.tools.files import copy, mkdir


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    _targets = ("c64", "apple2")

    def export_sources(self):
        copy(self, "hello.c", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "text.s", src=self.recipe_folder, dst=self.export_sources_folder)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        if can_run(self):
            for src in self.exports_sources:
                shutil.copy(os.path.join(self.source_folder, src), os.path.join(self.build_folder, src))
            for target in self._targets:
                output = f"hello_{target}"
                mkdir(self, target)
                try:
                    # Try removing the output file to give confidence it is created by cc65
                    os.unlink(output)
                except FileNotFoundError:
                    pass
                self.run(f"{os.environ['CC65']} -O -t {target} hello.c -o {target}/hello.s")
                self.run(f"{os.environ['AS65']} -t {target} {target}/hello.s -o {target}/hello.o")
                self.run(f"{os.environ['AS65']} -t {target} text.s -o {target}/text.o")
                self.run(
                    f"{os.environ['LD65']} -o {output} -t {target} "
                    f"{target}/hello.o {target}/text.o {target}.lib"
                )

    def test(self):
        if can_run(self):
            for target in self._targets:
                assert os.path.isfile(f"hello_{target}")
