from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("gobject-introspection/[^1.82]")

    def test(self):
        if can_run(self):
            self.run("g-ir-inspect Gio --print-shlibs --print-typelibs", env=["conanbuild", "conanrun"])
