import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class UserspaceRCUConan(ConanFile):
    name = "userspace-rcu"
    description = "Userspace RCU (read-copy-update) library"
    license = "LGPL-2.1"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://liburcu.org/"
    topics = "urcu"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Macos"]:
            raise ConanInvalidConfiguration(f"Building for {self.settings.os} unsupported")

    def build_requirements(self):
        self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = AutotoolsToolchain(self)
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        for lib_type in ["", "-bp", "-cds", "-mb", "-memb", "-qsbr", "-signal"]:
            if Version(self.version) >= "0.15" and lib_type == "-signal":
                continue
            component_name = f"urcu{lib_type}"
            self.cpp_info.components[component_name].set_property("pkg_config_name", f"lib{component_name}")
            self.cpp_info.components[component_name].libs = [component_name]
            self.cpp_info.components[component_name].requires = ["urcu-common"]

        self.cpp_info.components["urcu-common"].libs = ["urcu-common"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["urcu-common"].system_libs = ["pthread"]
