from io import StringIO

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackage(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        if can_run(self):
            output = StringIO()
            self.run("java --version", output, env="conanrun")
            self.output.info(f"Java version output: {output.getvalue()}")
            version_info = output.getvalue()
            if "openjdk" in version_info:
                pass
            else:
                raise ConanException("java call seems not use the openjdk bin")
