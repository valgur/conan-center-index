# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=1.53.0"


class LibNlConan(ConanFile):
    name = "libnl"
    description = (
        "A collection of libraries providing APIs to netlink protocol based Linux kernel interfaces."
    )
    license = "LGPL-2.1-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.infradead.org/~tgr/libnl/"
    topics = ("netlink",)

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

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Libnl is only supported on Linux")

    def build_requirements(self):
        self.tool_requires("flex/2.6.4")
        self.tool_requires("bison/3.7.6")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args = [f"--prefix={unix_path(self.package_folder)}"]
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.components["nl"].libs = ["nl-3"]
        self.cpp_info.components["nl"].includedirs = [os.path.join("include", "libnl3")]
        if self._settings_build.os != "Windows":
            self.cpp_info.components["nl"].system_libs = ["pthread", "m"]
        self.cpp_info.components["nl-route"].libs = ["nl-route-3"]
        self.cpp_info.components["nl-route"].requires = ["nl"]
        self.cpp_info.components["nl-genl"].libs = ["nl-genl-3"]
        self.cpp_info.components["nl-genl"].requires = ["nl"]
        self.cpp_info.components["nl-nf"].libs = ["nl-nf-3"]
        self.cpp_info.components["nl-nf"].requires = ["nl-route"]
        self.cpp_info.components["nl-cli"].libs = ["nl-cli-3"]
        self.cpp_info.components["nl-cli"].requires = ["nl-nf", "nl-genl"]
        self.cpp_info.components["nl-idiag"].libs = ["nl-idiag-3"]
        self.cpp_info.components["nl-idiag"].requires = ["nl"]
