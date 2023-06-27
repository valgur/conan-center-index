# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, get, load, save

required_conan_version = ">=1.33.0"


class UaNodeSetConan(ConanFile):
    name = "ua-nodeset"
    license = "MIT"
    description = "UANodeSets and other normative files which are released with a specification"
    homepage = "https://github.com/OPCFoundation/UA-Nodeset"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("opc-ua-specifications", "uanodeset", "normative-files", "companion-specification")

    no_copy_source = True

    def _extract_license(self):
        content = load(self, os.path.join(self.source_folder, "AnsiC", "opcua_clientapi.c"))
        license_contents = content[2 : content.find("*/", 1)]
        save(self, "LICENSE", license_contents)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        self._extract_license()
        copy(self, "*", dst=os.path.join(self.package_folder, "res"), src=self.source_folder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["res"]
