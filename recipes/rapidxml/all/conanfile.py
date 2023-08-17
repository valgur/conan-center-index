from conan import ConanFile
from conan.tools.files import copy, get, apply_conandata_patches, export_conandata_patches
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.52.0"


class RapiXMLConan(ConanFile):
    name = "rapidxml"
    description = "RapidXml is an attempt to create the fastest XML parser possible."
    license = ["BSL-1.0", "MIT"]
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://rapidxml.sourceforge.net"
    topics = ("xml", "parser", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)

    def package(self):
        copy(self, "license.txt",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "include", "rapidxml"))

    def package_info(self):
        self.cpp_info.includedirs.append(os.path.join("include", "rapidxml"))
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
