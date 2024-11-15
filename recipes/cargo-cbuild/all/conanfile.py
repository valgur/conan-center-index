import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get, download

required_conan_version = ">=1.47.0"


class CargoCBuildConan(ConanFile):
    name = "cargo-cbuild"
    description = "Cargo applet to build and install C-ABI compatible dynamic and static libraries."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/lu-zero/cargo-c"
    topics = ("rust", "cargo", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os == "Windows":
            if self.settings.arch != "x86_64":
                raise ConanInvalidConfiguration("cargo-cbuild is only available for x86_64 on Windows")
        if self.settings.os == "Macos":
            if self.settings.arch not in ["x86_64", "armv8"]:
                raise ConanInvalidConfiguration("cargo-cbuild is only available for x86_64 and armv8 on MacOS")
        if self.settings.os == "Linux":
            if str(self.settings.arch) not in self.conan_data["sources"][self.version][str(self.settings.os)]:
                raise ConanInvalidConfiguration(f"Unsupported arch: {self.settings.arch}")
        else:
            raise ConanInvalidConfiguration(f"Unsupported OS: {self.settings.os}")

    def build(self):
        info = self.conan_data["sources"][self.version][str(self.settings.os)]
        if self.settings.os == "Linux":
            info = info[str(self.settings.arch)]
        get(self, **info)
        download(self, **self.conan_data["sources"][self.version]["license"], filename="LICENSE")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "cargo-*", self.source_folder, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
