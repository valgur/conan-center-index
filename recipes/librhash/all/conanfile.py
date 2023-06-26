# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, chdir, copy, export_conandata_patches, get, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=1.53.0"


class LibRHashConan(ConanFile):
    name = "librhash"
    description = "Great utility for computing hash sums"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://rhash.sourceforge.net/"
    topics = ("rhash", "hash", "checksum")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openssl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openssl": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openssl:
            self.requires("openssl/1.1.1q")

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Visual Studio is not supported")

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        if self.settings.compiler in ("apple-clang",):
            if self.settings.arch in ("armv7",):
                tc.build_type_link_flags.append("-arch armv7")
            elif self.settings.arch in ("armv8",):
                tc.build_type_link_flags.append("-arch arm64")
        vars = tc.vars
        tc.configure_args = [
            (
                # librhash's configure script does not understand `--enable-opt1=yes`
                "--enable-openssl"
                if self.options.with_openssl
                else "--disable-openssl"
            ),
            "--disable-gettext",
            # librhash's configure script is custom and does not understand "--bindir=${prefix}/bin" arguments
            f"--prefix={unix_path(self.package_folder)}",
            f"--bindir={unix_path(self, os.path.join(self.package_folder, 'bin'))}",
            f"--libdir={unix_path(self, os.path.join(self.package_folder, 'lib'))}",
            # the configure script does not use CPPFLAGS, so add it to CFLAGS/CXXFLAGS
            f"--extra-cflags={'{} {}'.format(vars['CFLAGS'], vars['CPPFLAGS'])}",
            f"--extra-ldflags={vars['LDFLAGS']}",
        ]

        # with environment_append(self, {"BUILD_TARGET": get_gnu_triplet(self, str(self.settings.os), str(self.settings.arch), str(self.settings.compiler))}):
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
            autotools.make(target="install-lib-headers")
            with chdir(self, "librhash"):
                if self.options.shared:
                    autotools.make(target="install-so-link")
        rmdir(self, os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "LibRHash"
        self.cpp_info.names["cmake_find_package_multi"] = "LibRHash"
        self.cpp_info.names["pkg_config"] = "librhash"
        self.cpp_info.libs = ["rhash"]
