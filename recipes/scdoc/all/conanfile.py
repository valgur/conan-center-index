# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import chdir, copy, get, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class ScdocInstallerConan(ConanFile):
    name = "scdoc"
    description = "scdoc is a simple man page generator for POSIX systems written in C99."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://git.sr.ht/~sircmpwn/scdoc"
    topics = ("manpage", "documentation", "posix")

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

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if self.settings.os == "Windows" or is_apple_os(self):
            raise ConanInvalidConfiguration(f"Builds aren't supported on {self.settings.os}")

    def build_requirements(self):
        self.build_requires("make/4.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.make_args = [f"PREFIX={self.package_folder}"]
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        with chdir(self, self.source_folder):
            autotools.make()

    def package(self):
        autotools = Autotools(self)
        with chdir(self, self.source_folder):
            autotools.install()
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libdirs = []

        scdoc_root = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(scdoc_root))
        self.env_info.PATH.append(scdoc_root)
        self._chmod_plus_x(os.path.join(scdoc_root, "scdoc"))
        pkgconfig_variables = {
            "exec_prefix": "${prefix}/bin",
            "scdoc": "${exec_prefix}/scdoc",
        }
        self.cpp_info.set_property(
            "pkg_config_custom_content",
            "\n".join(f"{key}={value}" for key, value in pkgconfig_variables.items()),
        )
