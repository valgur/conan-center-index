from conan import ConanFile


class MinGWTestConan(ConanFile):
    settings = "os", "arch"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        self.run("gcc.exe --version")
