import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class libxftConan(ConanFile):
    name = "libxft"
    description = "X FreeType library"
    license = "HPND-sell-variant"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/lib/libxft"
    topics = ("x11", "xorg", "freetype")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_xorg_system": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_xorg_system": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.use_xorg_system:
            self.requires("xorg/system", transitive_headers=True)
        else:
            self.requires("xorg-proto/2024.1", transitive_headers=True)
            self.requires("libxrender/0.9.11", transitive_headers=True)
        self.requires("freetype/2.13.2", transitive_headers=True)
        self.requires("fontconfig/2.15.0", transitive_headers=True)

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        self.tool_requires("xorg-macros/1.20.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = AutotoolsToolchain(self)
        tc.generate()
        deps = PkgConfigDeps(self)
        deps.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "xft")
        self.cpp_info.set_property("cmake_target_aliases", ["X11::Xft"])
        self.cpp_info.libs = ["Xft"]
        self.cpp_info.requires = ["freetype::freetype", "fontconfig::fontconfig"]
        if self.options.use_xorg_system:
            self.cpp_info.requires.append("xorg::xrender")
        else:
            self.cpp_info.requires.extend(["xorg-proto::xorg-proto", "libxrender::libxrender"])
