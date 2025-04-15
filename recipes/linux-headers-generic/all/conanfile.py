import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.files import *
from conan.tools.gnu import Autotools, GnuToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class LinuxHeadersGenericConan(ConanFile):
    name = "linux-headers-generic"
    description = "Generic Linux kernel headers"
    license = "GPL-2.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.kernel.org/"
    topics = ("linux", "headers", "generic", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _linux_arch(self):
        arch = str(self.settings.arch)
        if arch in ["armv8", "armv8.3", "arm64ec"]:
            return "arm64"
        if arch.startswith("arm"):
            return "arm"
        return {
            "mips": "mips",
            "mips64": "mips",
            "ppc32": "powerpc",
            "ppc32be": "powerpc",
            "ppc64": "powerpc",
            "ppc64le": "powerpc",
            "riscv32": "riscv",
            "riscv64": "riscv",
            "s390": "s390",
            "s390x": "s390",
            "sh4le": "sh",
            "sparc": "sparc",
            "sparcv9": "sparc",
            "x86": "x86",
            "x86_64": "x86",
            "xtensalx106": "xtensa",
            "xtensalx6": "xtensa",
            "xtensalx7": "xtensa",
        }.get(arch)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.os
        del self.info.settings.build_type
        del self.info.settings.compiler

    def validate(self):
        if self.settings.os != "Linux" or self.settings_build.os != "Linux":
            raise ConanInvalidConfiguration("linux-headers-generic supports only Linux")
        if not self._linux_arch:
            raise ConanInvalidConfiguration(f"Unsupported architecture {self.settings.arch}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = GnuToolchain(self)
        tc_vars = tc.extra_env.vars(self)
        tc.make_args["ARCH"] = self._linux_arch
        # HOSTCC  scripts/basic/fixdep
        tc.make_args["HOSTCC"] = tc_vars.get("CC_FOR_BUILD" if cross_building(self) else "CC", "cc")
        tc.generate()

    def build(self):
        with chdir(self, self.build_folder):
            autotools = Autotools(self)
            autotools.make(target="headers", args=["-f", os.path.join(self.source_folder, "Makefile")])

    def package(self):
        copy(self, "COPYING",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "include/*.h",
             dst=self.package_folder,
             src=os.path.join(self.build_folder, "usr"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
