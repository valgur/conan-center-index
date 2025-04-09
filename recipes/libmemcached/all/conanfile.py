import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"

class LibmemcachedConan(ConanFile):
    name = "libmemcached"
    license = "BSD License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libmemcached.org/"
    description = "libmemcached is a C client library for interfacing to a memcached server"
    topics = ("cache", "network", "cloud")
    package_type = "library"

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "sasl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "sasl": False,
    }

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"] and not is_apple_os(self):
            raise ConanInvalidConfiguration(f"{self.ref} is not supported on {self.settings.os}.")

    def build_requirements(self):
        self.tool_requires("libtool/2.4.7")

    def _patch_source(self):
        # Disable tests. This avoids a test dependency on libuuid as well.
        save(self, os.path.join(self.source_folder, "libtest", "include.am"), "test:\t\n")
        save(self, os.path.join(self.source_folder, "tests", "include.am"), "test:\t\n")

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")
        tc = AutotoolsToolchain(self)
        tc.configure_args.append('--disable-dependency-tracking')
        if not self.options.sasl:
            tc.configure_args.append("--disable-sasl")
        tc.generate()
        AutotoolsDeps(self).generate()

    def build(self):
        self._patch_source()
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = ["memcached"]
        self.cpp_info.system_libs = ["m"]

