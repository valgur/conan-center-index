from conan import ConanFile
from conan.tools.gnu import PkgConfig
from conan.tools.layout import basic_layout
from conan.tools.system import package_manager
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=2.1"


class XkeyboardConfigConan(ConanFile):
    name = "xkeyboard-config"
    package_type = "application"
    url = "https://github.com/conan-io/conan-center-index"
    license = "HPND AND HPND-sell-variant AND X11 AND X11-distribute-modifications-variant AND MIT AND MIT-open-group AND xkeyboard-config-Zinoviev"
    homepage = "https://www.freedesktop.org/wiki/Software/XKeyboardConfig/"
    description = "The non-arch keyboard configuration database for X Window."
    settings = "os", "arch", "compiler", "build_type"
    topics = ("x11", "xorg", "keyboard")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("This recipe supports only Linux and FreeBSD")

    def system_requirements(self):
        apt = package_manager.Apt(self)
        apt.install(["xkb-data"], update=True, check=True)

        yum = package_manager.Yum(self)
        yum.install(["xkeyboard-config-devel"], update=True, check=True)

        dnf = package_manager.Dnf(self)
        dnf.install(["xkeyboard-config-devel"], update=True, check=True)

        zypper = package_manager.Zypper(self)
        zypper.install(["xkeyboard-config"], update=True, check=True)

        pacman = package_manager.PacMan(self)
        pacman.install(["xkeyboard-config"], update=True, check=True)

        package_manager.Pkg(self).install(["xkeyboard-config"], update=True, check=True)

    def package_info(self):
        pkg_config = PkgConfig(self, "xkeyboard-config")
        pkg_config.fill_cpp_info(self.cpp_info, is_system=self.settings.os != "FreeBSD")
        self.cpp_info.set_property("pkg_config_name", "xkeyboard-config")
        self.cpp_info.set_property("component_version", pkg_config.version)
        self.cpp_info.set_property("pkg_config_custom_content", "\n".join(
            f"{key}={value}"
            for key, value in pkg_config.variables.items()
            if key not in ["pcfiledir", "prefix", "includedir"]
        ))
