import re

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout
from six import StringIO


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        if can_run(self):
            output = StringIO()
            self.run("cmake --version", output, env="conanrun")
            output_str = str(output.getvalue())
            self.output.info(f"Installed version: {output_str}")
            tokens = re.split('[@#]', self.tested_reference_str)
            require_version = tokens[0].split("/", 1)[1]
            self.output.info(f"Expected version: {require_version}")
            assert_cmake_version = f"cmake version {require_version}"
            assert(assert_cmake_version in output_str)
