from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.system import package_manager
from conan.tools.gnu import PkgConfig

required_conan_version = ">=1.50.0"


class LibUDEVConan(ConanFile):
    name = "libudev"
    description = "API for enumerating and introspecting local devices"
    license = ("GPL-2.0-or-later", "LGPL-2.1-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.freedesktop.org/software/systemd/man/udev.html"
    topics = ("udev", "devices", "enumerating")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("libudev is only supported on Linux.")

    def system_requirements(self):
        dnf = package_manager.Dnf(self)
        dnf.install(["systemd-devel"], update=True, check=True)

        yum = package_manager.Yum(self)
        yum.install(["systemd-devel"], update=True, check=True)

        apt = package_manager.Apt(self)
        apt.install(["libudev-dev"], update=True, check=True)

        pacman = package_manager.PacMan(self)
        pacman.install(["systemd-libs"], update=True, check=True)

        zypper = package_manager.Zypper(self)
        zypper.install_substitutes(["libudev-devel"], ["systemd-devel"], update=True, check=True)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        pkg_config = PkgConfig(self, "libudev")
        pkg_config.fill_cpp_info(self.cpp_info)
