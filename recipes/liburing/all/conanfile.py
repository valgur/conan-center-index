# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, export_conandata_patches
from conan.tools.files import get, chdir, rmdir, copy
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class LiburingConan(ConanFile):
    name = "liburing"
    description = (
        "helpers to setup and teardown io_uring instances, and also a "
        "simplified interface for applications that don't need (or want) "
        "to deal with the full kernel side implementation."
    )
    license = "GPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/axboe/liburing"
    topics = ("asynchronous-io", "async", "kernel")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libc": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libc": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "2.2":
            self.options.rm_safe("with_libc")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("linux-headers-generic/5.13.9")

    def validate(self):
        # FIXME: use kernel version of build/host machine.
        # kernel version should be encoded in profile
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("liburing is supported only on linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        if self.options.get_safe("with_libc") == False:
            tc.configure_args.append("--nolibc")
        tc.extra_cflags.append("-std=gnu99")
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            install_args = [f"ENABLE_SHARED={1 if self.options.shared else 0}"]
            autotools.install(args=install_args)

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "man"))

        if self.options.shared:
            os.remove(os.path.join(self.package_folder, "lib", "liburing.a"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "liburing")
        self.cpp_info.libs = ["uring"]
