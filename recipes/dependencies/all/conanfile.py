import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class DependenciesConan(ConanFile):
    name = "dependencies"
    description = ("Dependencies can help Windows developers troubleshooting their DLL-loading dependency issues. "
                   "It is a rewrite of the legacy Dependency Walker software, which was shipped along Windows SDKs, "
                   "but whose development stopped around 2006.")
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/lucasg/Dependencies"
    topics = ("windows", "dll", "debugging", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Dependencies is only available on Windows")
        if self.settings.arch not in ["x86_64", "x86"]:
            raise ConanInvalidConfiguration("Dependencies is only available for x86_64 and x86 architectures")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.arch)], strip_root=False)
        download(self, **self.conan_data["sources"][self.version]["license"], filename="LICENSE")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.exe", self.source_folder, os.path.join(self.package_folder, "bin"))
        copy(self, "*.dll", self.source_folder, os.path.join(self.package_folder, "bin"),
             excludes=["msvcp*.dll", "msvcr*.dll", "vcruntime*.dll"])
        copy(self, "*.config", self.source_folder, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
