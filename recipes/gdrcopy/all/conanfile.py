import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class GdrcopyConan(ConanFile):
    name = "gdrcopy"
    description = "A fast GPU memory copy library based on NVIDIA GPUDirect RDMA technology"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://developer.nvidia.com/gdrcopy"
    topics = ("nvidia", "gpu-memory", "kernel-mode-driver", "gpudirect-rdma")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    languages = ["C"]
    options = {
        "tools": [True, False],
    }
    default_options = {
        "tools": False,
    }

    def package_id(self):
        self.info.settings.build_type = "Release"

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("gdrcopy can only be built on Linux.")
        # https://github.com/NVIDIA/gdrcopy/blob/v2.5/include/gdrconfig.h
        if self.settings.arch not in ["x86_64", "armv8", "ppc64le"]:
            raise ConanInvalidConfiguration(f"gdrcopy does not support {self.settings.arch} architecture.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc_vars = tc.vars()
        tc.make_args.append(f"CC={tc_vars.get('CC', 'cc')}")
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.make(target="lib")
            if self.options.tools:
                autotools.make(target="exes")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install(target="lib_install", args=["prefix=/"])
            if self.options.tools:
                autotools.install(target="exes_install", args=["prefix=/"])

    def package_info(self):
        self.cpp_info.libs = ["gdrapi"]
