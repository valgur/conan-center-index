from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import copy, get, rm, rmdir, chdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
import os


required_conan_version = ">=2.0.9"

class SysfsutilsConan(ConanFile):
    name = "sysfsutils"
    description = "Library used in handling linux kernel sysfs mounts and their various files."
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/linux-ras/sysfsutils"
    topics = ("sysfs")
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

    tool_requires = ("libtool/2.4.7")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")


    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.name} only supports Linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")
        tc = AutotoolsToolchain(self)
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        with chdir(self, os.path.join(self.source_folder, "lib")):
            autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"),
             os.path.join(self.package_folder, "include", "sysfs"))
        autotools = Autotools(self)
        with chdir(self, os.path.join(self.source_folder, "lib")):
            autotools.install()

        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["sysfs"]
        self.cpp_info.set_property("pkg_config_name", "libsysfs")

