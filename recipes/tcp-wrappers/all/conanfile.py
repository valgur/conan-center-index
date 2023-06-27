# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import apply_conandata_patches, chdir, copy, export_conandata_patches, get
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path, is_msvc

required_conan_version = ">=1.53.0"


class TcpWrappersConan(ConanFile):
    name = "tcp-wrappers"
    description = "A security tool which acts as a wrapper for TCP daemons"
    license = "BSD"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "ftp://ftp.porcupine.org/pub/security/index.html"
    topics = ("tcp", "ip", "daemon", "wrapper")

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

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("Visual Studio is not supported")
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("tcp_wrappers_{}-ipv6.4".format(self.version), self.source_folder)

    def generate(self):
        # TODO: fill in generate()
        pass

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            autotools = AutoToolsBuildEnvironment(self)
            make_args = [
                "REAL_DAEMON_DIR={}".format(unix_path(self, os.path.join(self.package_folder, "bin"))),
                "-j1",
                "SHEXT={}".format(self._shext),
            ]
            if self.options.shared:
                make_args.append("shared=1")
            env_vars = autotools.vars
            if self.options.get_safe("fPIC", True):
                env_vars["CFLAGS"] += " -fPIC"
            env_vars["ENV_CFLAGS"] = env_vars["CFLAGS"]
            # env_vars["SHEXT"] = self._shext
            print(env_vars)
            with environment_append(self, env_vars):
                autotools.make(target="linux", args=make_args)

    @property
    def _shext(self):
        if is_apple_os(self.settings.os):
            return ".dylib"
        return ".so"

    def package(self):
        copy(
            self,
            pattern="DISCLAIMER",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        for exe in ("safe_finger", "tcpd", "tcpdchk", "tcpdmatch", "try-from"):
            copy(
                self,
                exe,
                src=self.source_folder,
                dst=os.path.join(self.package_folder, "bin"),
                keep_path=False,
            )
        copy(
            self,
            "tcpd.h",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "include"),
            keep_path=False,
        )
        if self.options.shared:
            copy(
                self,
                "libwrap{}".format(self._shext),
                src=self.source_folder,
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )
        else:
            copy(
                self,
                "libwrap.a",
                src=self.source_folder,
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )

    def package_info(self):
        self.cpp_info.libs = ["wrap"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
