import os

from conan import ConanFile
from conan.tools.files import *

required_conan_version = ">=2.0"


class PackageConan(ConanFile):
    name = "package"
    description = "short description"
    license = ""  # Use short name only, conform to SPDX License List: https://spdx.org/licenses/
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/project/package"
    # include "pre-built" for pre-built packages
    topics = ("topic1", "topic2", "topic3", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def build(self):
        # self.settings is not supported in source(), so fetch the binaries in build() instead
        get(self, **self.conan_data["sources"][self.version][str(self.settings.os)][str(self.settings.arch)], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.exe", self.source_folder, os.path.join(self.package_folder, "bin"))
        copy(self, "foo", self.source_folder, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
