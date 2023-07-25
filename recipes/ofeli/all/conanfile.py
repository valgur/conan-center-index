# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import chdir, copy, get
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class OfeliConan(ConanFile):
    name = "ofeli"
    description = "An Object Finite Element Library"
    license = "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://ofeli.org/index.html"
    topics = ("finite-element", "finite-element-library", "finite-element-analysis", "finite-element-solver")

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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    @property
    def _doc_folder(self):
        return os.path.join(self.source_folder, "doc")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("Ofeli is just supported for Linux")
        if self.settings.compiler != "gcc":
            raise ConanInvalidConfiguration("Ofeli is just supported for GCC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)
        if self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Ofeli supports only libstdc++'s new ABI")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args += [f"--enable-{'release' if self.settings.build_type == 'Release' else 'debug'}"]
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(
            self,
            "*libofeli.a",
            dst=os.path.join(self.package_folder, "lib"),
            src=os.path.join(self.source_folder, "src"),
        )
        copy(
            self,
            "*.md",
            dst=os.path.join(self.package_folder, "res"),
            src=os.path.join(self.source_folder, "material"),
        )
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self._doc_folder)

    def package_info(self):
        self.cpp_info.libs = ["ofeli"]
        self.env_info.OFELI_PATH_MATERIAL.append(os.path.join(self.package_folder, "res"))
