import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"

class MozillaBuildConan(ConanFile):
    name = "mozilla-build"
    homepage = "https://wiki.mozilla.org/MozillaBuild"
    description = "Mozilla build requirements on Windows"
    topics = ("mozilla", "build")
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    license = "MPL-2.0"

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Only Windows supported")

    def build_requirements(self):
        self.tool_requires("7zip/22.01")

    def build(self):
        filename = "mozilla-build.exe"
        download(self, **self.conan_data["sources"][self.version][0], filename=filename)
        download(self, **self.conan_data["sources"][self.version][1], filename="LICENSE")
        self.run(f"7z x {filename}")

    def package(self):
        copy(self, "LICENSE", src=self.build_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "nsinstall.exe", src=os.path.join(self.build_folder, "bin"), dst=os.path.join(self.package_folder, "bin"))

    def package_id(self):
        del self.info.settings.build_type
        del self.info.settings.compiler

    def package_info(self):
        self.cpp_info.includedirs = []
