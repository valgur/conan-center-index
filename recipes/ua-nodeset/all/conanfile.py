# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, get, load, save

required_conan_version = ">=1.47.0"


class UaNodeSetConan(ConanFile):
    name = "ua-nodeset"
    description = "UANodeSets and other normative files which are released with a specification"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/OPCFoundation/UA-Nodeset"
    topics = ("opc-ua-specifications", "uanodeset", "normative-files", "companion-specification", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def build(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _extract_license(self):
        content = load(self, os.path.join(self.source_folder, "AnsiC", "opcua_clientapi.c"))
        license_contents = content[2 : content.find("*/", 1)]
        save(self, "LICENSE", license_contents)

    def package(self):
        self._extract_license()
        copy(self, "*", dst=os.path.join(self.package_folder, "res"), src=self.source_folder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["res"]
