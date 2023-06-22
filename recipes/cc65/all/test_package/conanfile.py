from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"
    exports_sources = "hello.c", "text.s"

    _targets = ("c64", "apple2")

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        if not tools.cross_building(self.settings):
            for src in self.exports_sources:
                shutil.copy(os.path.join(self.source_folder, src), os.path.join(self.build_folder, src))
            for target in self._targets:
                output = "hello_{}".format(target)
                tools.mkdir(target)
                try:
                    # Try removing the output file to give confidence it is created by cc65
                    os.unlink(output)
                except FileNotFoundError:
                    pass
                self.run("{p} -O -t {t} hello.c -o {t}/hello.s".format(p=os.environ["CC65"], t=target))
                self.run("{p} -t {t} {t}/hello.s -o {t}/hello.o".format(p=os.environ["AS65"], t=target))
                self.run("{p} -t {t} text.s -o {t}/text.o".format(p=os.environ["AS65"], t=target))
                self.run(
                    "{p} -o {o} -t {t} {t}/hello.o {t}/text.o {t}.lib".format(
                        o=output, p=os.environ["LD65"], t=target
                    )
                )

    def test(self):
        if can_run(self):
            for target in self._targets:
                assert os.path.isfile(f"hello_{target}")
