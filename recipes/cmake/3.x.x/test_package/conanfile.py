import re

from conan import ConanFile
from conan.tools.layout import basic_layout
from six import StringIO


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        output = StringIO()
        # Third arg to self.run renamed "stdout" in Conan 2.0 but 1.x linter doesn't like it
        self.run("cmake --version", output)
        output_str = str(output.getvalue())
        self.output.info(f"Installed version: {output_str}")
        tokens = re.split('[@#]', self.tested_reference_str)
        require_version = tokens[0].split("/", 1)[1]
        self.output.info(f"Expected version: {require_version}")
        assert_cmake_version = "cmake version %s" % require_version
        assert(assert_cmake_version in output_str)
