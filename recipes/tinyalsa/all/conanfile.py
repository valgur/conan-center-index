import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, chdir, copy, export_conandata_patches, get, rmdir, rm
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class TinyAlsaConan(ConanFile):
    name = "tinyalsa"
    description = "A small library to interface with ALSA in the Linux kernel"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/tinyalsa/tinyalsa"
    topics = ("tiny", "alsa", "sound", "audio", "tinyalsa")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_utils": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_utils": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration(f"{self.name} only works for Linux.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.make_args = ["PREFIX=/"]
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        copy(self, "NOTICE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)

        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))

        if not self.options.with_utils:
            rmdir(self, os.path.join(self.package_folder, "bin"))

        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*.so*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["tinyalsa"]
        if Version(self.version) >= "2.0.0":
            self.cpp_info.system_libs.append("dl")

        # TODO: Legacy, to be removed on Conan 2.0
        if self.options.with_utils:
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info(f"Appending PATH environment variable: {bin_path}")
            self.env_info.path.append(bin_path)
