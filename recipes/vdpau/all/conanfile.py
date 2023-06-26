# Warnings:
#   Disallowed attribute 'version = 'system''
#   Missing required method 'config_options'
#   Missing required method 'configure'
#   Missing required method 'source'
#   Missing required method 'generate'
#   Missing required method 'build'
#   Missing required method 'package'

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.gnu import PkgConfig
from conan.tools.system import package_manager

required_conan_version = ">=1.53.0"


class SysConfigVDPAUConan(ConanFile):
    name = "vdpau"
    description = (
        "VDPAU is the Video Decode and Presentation API for UNIX. It provides an interface to video decode"
        " acceleration and presentation hardware present in modern GPUs."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.freedesktop.org/wiki/Software/VDPAU/"
    topics = ("hwaccel", "video")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        pass

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("This recipe supports only Linux and FreeBSD")

    def system_requirements(self):
        dnf = package_manager.Dnf(self)
        dnf.install(["libvdpau-devel"], update=True, check=True)

        yum = package_manager.Yum(self)
        yum.install(["libvdpau-devel"], update=True, check=True)

        apt = package_manager.Apt(self)
        apt.install(["libvdpau-dev"], update=True, check=True)

        pacman = package_manager.PacMan(self)
        pacman.install(["libvdpau"], update=True, check=True)

        zypper = package_manager.Zypper(self)
        zypper.install(["libvdpau-devel"], update=True, check=True)

        pkg = package_manager.Pkg(self)
        pkg.install(["libvdpau"], update=True, check=True)

    def source(self):
        # TODO: fill in source()
        pass

    def generate(self):
        # TODO: fill in generate()
        pass

    def build(self):
        # TODO: fill in build()
        pass

    def package(self):
        # TODO: fill in package()
        pass

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            pkg_config = PkgConfig(self, "vdpau")
            pkg_config.fill_cpp_info(self.cpp_info)
