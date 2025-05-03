from conan import ConanFile
from conan.tools.gnu import PkgConfig
from conan.tools.system import package_manager

required_conan_version = ">=2.1"


class GbmSystemConan(ConanFile):
    name = "gbm"
    version = "system"
    description = "Virtual Conan package for GBM support"
    topics = ("mesa", "graphics")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://mesa3d.org/"
    license = "MIT"
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        self.info.clear()

    def system_requirements(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            return

        dnf = package_manager.Dnf(self)
        dnf.install_substitutes(["libgbm-devel"], update=True, check=True)

        yum = package_manager.Yum(self)
        yum.install(["libgbm-devel"], update=True, check=True)

        apt = package_manager.Apt(self)
        apt.install_substitutes(["libgbm-dev"], update=True, check=True)

        pacman = package_manager.PacMan(self)
        pacman.install(["libgbm"], update=True, check=True)

        zypper = package_manager.Zypper(self)
        zypper.install_substitutes(["libgbm-devel"], update=True, check=True)

        pkg = package_manager.Pkg(self)
        pkg.install(["libgbm"], update=True, check=True)

        pkg_util = package_manager.PkgUtil(self)
        pkg_util.install(["mesalibs"], update=True, check=True)

    def package_info(self):
        pkg_config = PkgConfig(self, "gbm")
        pkg_config.fill_cpp_info(self.cpp_info, is_system=True)
        self.cpp_info.version = pkg_config.version
        self.cpp_info.set_property("pkg_config_name", "gbm")
        self.cpp_info.set_property("component_version", pkg_config.version)
        self.cpp_info.bindirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property(
            "pkg_config_custom_content",
            "\n".join(f"{key}={value}" for key, value in pkg_config.variables.items() if key not in ["pcfiledir", "prefix", "includedir"])
        )
