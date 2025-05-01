import os
from pathlib import Path

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class RenderdocConan(ConanFile):
    name = "renderdoc"
    description = "API for RenderDoc, a stand-alone graphics debugger"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://renderdoc.org/"
    topics = ("graphics", "debugging", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        download(self, **self.conan_data["sources"][self.version]["renderdoc_app.h"], filename="renderdoc_app.h")

    def _write_license(self):
        dest = Path(self.package_folder, "licenses", "LICENSE")
        license_text = Path(self.source_folder, "renderdoc_app.h").read_text(encoding="utf-8").split("#pragma once", 1)[0]
        license_text = "\n".join(l[3:] for l in license_text.splitlines()[1:-2])
        dest.parent.mkdir()
        dest.write_text(license_text, encoding="utf-8")

    def package(self):
        self._write_license()
        copy(self, "renderdoc_app.h", self.source_folder, os.path.join(self.package_folder, "include", "renderdoc", "app"))

    def package_info(self):
        self.cpp_info.includedirs.append(os.path.join("include", "renderdoc"))
        self.cpp_info.includedirs.append(os.path.join("include", "renderdoc", "app"))
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
