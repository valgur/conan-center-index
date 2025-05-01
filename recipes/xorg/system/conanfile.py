from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.gnu import PkgConfig
from conan.tools.layout import basic_layout
from conan.tools.system import package_manager

required_conan_version = ">=2.1"


class XorgConan(ConanFile):
    name = "xorg"
    description = "The X.Org project provides an open source implementation of the X Window System."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.x.org/wiki/"
    topics = ("x11", "xorg")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("This recipe supports only Linux and FreeBSD")

    def system_requirements(self):
        apt = package_manager.Apt(self)
        apt.install([
                "libfontenc-dev",
                "libice-dev",
                "libsm-dev",
                "libx11-dev",
                "libx11-xcb-dev",
                "libxau-dev",
                "libxaw7-dev",
                "libxcb-composite0-dev",
                "libxcb-cursor-dev",
                "libxcb-dri2-0-dev",
                "libxcb-dri3-dev",
                "libxcb-ewmh-dev",
                "libxcb-glx0-dev",
                "libxcb-icccm4-dev",
                "libxcb-image0-dev",
                "libxcb-keysyms1-dev",
                "libxcb-present-dev",
                "libxcb-randr0-dev",
                "libxcb-render-util0-dev",
                "libxcb-render0-dev",
                "libxcb-res0-dev",
                "libxcb-shape0-dev",
                "libxcb-sync-dev",
                "libxcb-xfixes0-dev",
                "libxcb-xinerama0-dev",
                "libxcb-xkb-dev",
                "libxcomposite-dev",
                "libxcursor-dev",
                "libxdamage-dev",
                "libxdmcp-dev",
                "libxext-dev",
                "libxfixes-dev",
                "libxi-dev",
                "libxinerama-dev",
                "libxkbfile-dev",
                "libxmu-dev",
                "libxmuu-dev",
                "libxpm-dev",
                "libxrandr-dev",
                "libxrender-dev",
                "libxres-dev",
                "libxss-dev",
                "libxt-dev",
                "libxtst-dev",
                "libxv-dev",
                "libxxf86vm-dev",
                "uuid-dev",
            ],
            update=True,
            check=True,
        )
        apt.install_substitutes(
            ["libxcb-util-dev"],
            ["libxcb-util0-dev"],
            update=True,
            check=True
        )

        yum = package_manager.Yum(self)
        yum.install([
                "libXScrnSaver-devel",
                "libXaw-devel",
                "libXcomposite-devel",
                "libXcursor-devel",
                "libXdamage-devel",
                "libXdmcp-devel",
                "libXinerama-devel",
                "libXrandr-devel",
                "libXres-devel",
                "libXtst-devel",
                "libXv-devel",
                "libXxf86vm-devel",
                "libfontenc-devel",
                "libuuid-devel",
                "libxcb-devel",
                "libxkbfile-devel",
                "xcb-util-cursor-devel",
                "xcb-util-devel",
                "xcb-util-image-devel",
                "xcb-util-keysyms-devel",
                "xcb-util-renderutil-devel",
                "xcb-util-wm-devel",
            ],
            update=True,
            check=True,
        )

        dnf = package_manager.Dnf(self)
        dnf.install([
                "libXScrnSaver-devel",
                "libXaw-devel",
                "libXcomposite-devel",
                "libXcursor-devel",
                "libXdamage-devel",
                "libXdmcp-devel",
                "libXinerama-devel",
                "libXrandr-devel",
                "libXres-devel",
                "libXtst-devel",
                "libXv-devel",
                "libXxf86vm-devel",
                "libfontenc-devel",
                "libuuid-devel",
                "libxcb-devel",
                "libxkbfile-devel",
                "xcb-util-cursor-devel",
                "xcb-util-devel",
                "xcb-util-image-devel",
                "xcb-util-keysyms-devel",
                "xcb-util-renderutil-devel",
                "xcb-util-wm-devel",
            ],
            update=True,
            check=True,
        )

        zypper = package_manager.Zypper(self)
        zypper.install([
                "libXaw-devel",
                "libXcomposite-devel",
                "libXcursor-devel",
                "libXdamage-devel",
                "libXdmcp-devel",
                "libXinerama-devel",
                "libXrandr-devel",
                "libXres-devel",
                "libXss-devel",
                "libXtst-devel",
                "libXv-devel",
                "libXxf86vm-devel",
                "libfontenc-devel",
                "libuuid-devel",
                "libxcb-devel",
                "libxkbfile-devel",
                "xcb-util-cursor-devel",
                "xcb-util-devel",
                "xcb-util-image-devel",
                "xcb-util-keysyms-devel",
                "xcb-util-renderutil-devel",
                "xcb-util-wm-devel",
            ],
            update=True,
            check=True,
        )

        pacman = package_manager.PacMan(self)
        pacman.install([
                "libfontenc",
                "libice",
                "libsm",
                "libxaw",
                "libxcb",
                "libxcomposite",
                "libxcursor",
                "libxdamage",
                "libxdmcp",
                "libxinerama",
                "libxkbfile",
                "libxrandr",
                "libxres",
                "libxss",
                "libxtst",
                "libxv",
                "libxxf86vm",
                "util-linux-libs",
                "xcb-util",
                "xcb-util-cursor",
                "xcb-util-image",
                "xcb-util-keysyms",
                "xcb-util-renderutil",
                "xcb-util-wm",
            ],
            update=True,
            check=True,
        )

        pkg = package_manager.Pkg(self)
        pkg.install([
                "libX11",
                "libXScrnSaver",
                "libfontenc",
                "libice",
                "libsm",
                "libxaw",
                "libxcomposite",
                "libxcursor",
                "libxdamage",
                "libxdmcp",
                "libxinerama",
                "libxkbfile",
                "libxrandr",
                "libxres",
                "libxtst",
                "libxv",
                "libxxf86vm",
                "xcb-util",
                "xcb-util-cursor",
                "xcb-util-image",
                "xcb-util-keysyms",
                "xcb-util-renderutil",
                "xcb-util-wm",
                "xkeyboard-config",
            ],
            update=True,
            check=True,
        )

        alpine = package_manager.Apk(self)
        alpine.install([
                "libfontenc-dev",
                "libice-dev",
                "libsm-dev",
                "libx11-dev",
                "libxau-dev",
                "libxaw-dev",
                "libxcb-dev",
                "libxcomposite-dev",
                "libxcursor-dev",
                "libxdamage-dev",
                "libxdmcp-dev",
                "libxext-dev",
                "libxfixes-dev",
                "libxi-dev",
                "libxinerama-dev",
                "libxkbfile-dev",
                "libxmu-dev",
                "libxpm-dev",
                "libxrandr-dev",
                "libxrender-dev",
                "libxres-dev",
                "libxscrnsaver-dev",
                "libxt-dev",
                "libxtst-dev",
                "libxv-dev",
                "libxxf86vm-dev",
                "xcb-util-cursor-dev",
                "xcb-util-dev",
                "xcb-util-image-dev",
                "xcb-util-keysyms-dev",
                "xcb-util-renderutil-dev",
                "xcb-util-wm-dev",
            ],
            update=True,
            check=True,
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []

        pkgs = [
            "fontenc",
            "ice",
            "sm",
            "x11",
            "x11-xcb",
            "xau",
            "xaw7",
            "xcb",
            "xcb-atom",
            "xcb-aux",
            "xcb-composite",
            "xcb-cursor",
            "xcb-dri2",
            "xcb-dri3",
            "xcb-event",
            "xcb-ewmh",
            "xcb-glx",
            "xcb-icccm",
            "xcb-image",
            "xcb-keysyms",
            "xcb-present",
            "xcb-randr",
            "xcb-render",
            "xcb-renderutil",
            "xcb-res",
            "xcb-shape",
            "xcb-shm",
            "xcb-sync",
            "xcb-util",
            "xcb-xfixes",
            "xcb-xinerama",
            "xcb-xkb",
            "xcomposite",
            "xcursor",
            "xdamage",
            "xdmcp",
            "xext",
            "xfixes",
            "xi",
            "xinerama",
            "xkbfile",
            "xmu",
            "xmuu",
            "xpm",
            "xrandr",
            "xrender",
            "xres",
            "xscrnsaver",
            "xt",
            "xtst",
            "xv",
            "xxf86vm",
        ]
        if self.settings.os != "FreeBSD":
            pkgs.append("uuid")

        for name in pkgs:
            pkg_config = PkgConfig(self, name)
            pkg_config.fill_cpp_info(self.cpp_info.components[name], is_system=self.settings.os != "FreeBSD")
            self.cpp_info.components[name].version = pkg_config.version
            self.cpp_info.components[name].set_property("pkg_config_name", name)
            self.cpp_info.components[name].set_property("component_version", pkg_config.version)
            self.cpp_info.components[name].bindirs = []
            self.cpp_info.components[name].includedirs = []
            self.cpp_info.components[name].libdirs = []
            self.cpp_info.components[name].set_property(
                "pkg_config_custom_content",
                "\n".join(f"{key}={value}" for key, value in pkg_config.variables.items() if key not in ["pcfiledir","prefix", "includedir"])
            )

        if self.settings.os == "Linux":
            self.cpp_info.components["sm"].requires.append("uuid")
