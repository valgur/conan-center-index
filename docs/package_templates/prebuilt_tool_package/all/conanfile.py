from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.files import get, copy
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration
import os


required_conan_version = ">=1.47.0"


class PackageConan(ConanFile):
    name = "package"
    description = "short description"
    license = ""
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/project/package"
    topics = ("topic1", "topic2", "topic3", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if is_apple_os(self) and Version(self.settings.os.version) < 11:
            raise ConanInvalidConfiguration(f"{self.ref} requires OSX >=11.")

    def source(self):
        pass

    def build(self):
        get(
            self,
            **self.conan_data["sources"][self.version][str(self.settings.os)][str(self.settings.arch)],
            strip_root=True,
        )

    def package(self):
        copy(
            self,
            pattern="LICENSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="*.exe",
            dst=os.path.join(self.package_folder, "bin"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="foo",
            dst=os.path.join(self.package_folder, "bin"),
            src=self.source_folder,
        )

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bin_folder = os.path.join(self.package_folder, "bin")
        self.env_info.PATH.append(bin_folder)
