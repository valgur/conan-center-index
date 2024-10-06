import os

from conan import ConanFile
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rmdir
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain

required_conan_version = ">=1.53.0"


class XFontsEncodingsConan(ConanFile):
    name = "xfonts-encodings"
    description = "Font encoding tables for libfontenc"
    license = "DocumentRef-COPYING:LicenseRef-xfonts-encodings-public-domain"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/font/encodings"
    topics = ("xorg", "x11")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("mkfontscale/[*]")
        # Also requires gzip, assumed to be available on the system

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = MesonToolchain(self)
        tc.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        os.rename(os.path.join(self.package_folder, "usr", "share"),
                  os.path.join(self.package_folder, "res"))
        rmdir(self, os.path.join(self.package_folder, "usr"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.resdirs = ["res"]

        encodings_dir = os.path.join(self.package_folder, "res", "fonts", "X11", "encodings", "encodings.dir")
        self.runenv_info.define_path("FONT_ENCODINGS_DIRECTORY", encodings_dir)
