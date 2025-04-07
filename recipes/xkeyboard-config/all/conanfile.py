import os

from conan import ConanFile
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rmdir, replace_in_file
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain

required_conan_version = ">=2.1"


class XkeyboardConfigConan(ConanFile):
    name = "xkeyboard-config"
    description = "Keyboard configuration database for X11"
    license = "HPND AND HPND-sell-variant AND X11 AND X11-distribute-modifications-variant AND MIT AND MIT-open-group AND xkeyboard-config-Zinoviev"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xkeyboard-config/xkeyboard-config"
    topics = ("xorg", "x11", "keyboard")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Android"]:
            raise ConanInvalidConfiguration("This recipe supports only Linux and FreeBSD")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        pass

    # def validate(self):
    #     if is_msvc(self):
    #         raise ConanInvalidConfiguration("MSVC is not supported.")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("gettext/0.22.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = MesonToolchain(self)
        tc.generate()
        deps = PkgConfigDeps(self)
        deps.generate()

    def _patch_sources(self):
        replace_in_file(self, os.path.join(self.source_folder, "meson.build"),
                        "enable_pytest = ", "enable_pytest = false #")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "share", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        os.rename(os.path.join(self.package_folder, "share"),
                  os.path.join(self.package_folder, "res"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "xkeyboard-config")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = ["res"]

        self.cpp_info.set_property("pkg_config_custom_content", "\n".join([
            "datadir=${prefix}/res",
            "xkb_base=${datadir}/X11/xkb"
        ]))
