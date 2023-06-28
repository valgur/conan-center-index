# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import collect_libs, copy, get, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class LibfabricConan(ConanFile):
    name = "libfabric"
    description = "Open Fabric Interfaces"
    license = ("BSD-2-Clause", "GPL-2.0-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://libfabric.org"
    topics = ("fabric", "communication", "framework", "service")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "gni": "ANY",
        "psm": "ANY",
        "psm2": "ANY",
        "psm3": "ANY",
        "rxm": "ANY",
        "sockets": "ANY",
        "tcp": "ANY",
        "udp": "ANY",
        "usnic": "ANY",
        "verbs": "ANY",
        "bgq": "ANY",
        "with_libnl": "ANY",
        "with_bgq_progress": [None, "auto", "manual"],
        "with_bgq_mr": [None, "basic", "scalable"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "gni": "auto",
        "psm": "auto",
        "psm2": "auto",
        "psm3": "auto",
        "rxm": "auto",
        "sockets": "auto",
        "tcp": "auto",
        "udp": "auto",
        "usnic": "auto",
        "verbs": "auto",
        "bgq": "auto",
        "with_libnl": None,
        "with_bgq_progress": None,
        "with_bgq_mr": None,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Macos"]:
            raise ConanInvalidConfiguration("libfabric only builds on Linux, Macos, and FreeBSD.")
        for p in self._providers:
            if self.options.get_safe(p) not in ["auto", "yes", "no", "dl"] and not os.path.isdir(
                str(self.options.get_safe(p))
            ):
                raise ConanInvalidConfiguration(
                    "Option {} can only be one of 'auto', 'yes', 'no', 'dl' or a directory path"
                )
        if self.options.get_safe("with_libnl") and not os.path.isdir(str(self.options.with_libnl)):
            raise ConanInvalidConfiguration("Value of with_libnl must be an existing directory")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        args = []
        for p in self._providers:
            args.append(f"--enable-{p}={self.options.get_safe(p)}")
        if self.options.with_libnl:
            args.append(f"--with-libnl={self.options.with_libnl}")
        if self.options.with_bgq_progress:
            args.append(f"--with-bgq-progress={self.options.with_bgq_progress}")
        if self.options.with_bgq_mr:
            args.append(f"--with-bgq-mr={self.options.with_bgq_mr}")
        tc.configure_args = args

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        autotools = Autotools()
        autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libfabric")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "m"]
