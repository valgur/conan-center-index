# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager

required_conan_version = ">=1.29.1"


class ResiprocateConan(ConanFile):
    name = "resiprocate"
    description = "The project is dedicated to maintaining a complete, correct, and commercially usable implementation of SIP and a few related protocols. "
    topics = ("sip", "voip", "communication", "signaling")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.resiprocate.org"
    license = "VSL-1.0"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "with_ssl": [True, False],
        "with_postgresql": [True, False],
        "with_mysql": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "with_ssl": True,
        "with_postgresql": True,
        "with_mysql": True,
    }
    _autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.os in ("Windows", "Macos"):
            # FIXME: Visual Studio project & Mac support seems available in resiprocate
            raise ConanInvalidConfiguration(
                "reSIProcate recipe does not currently support {}.".format(self.settings.os)
            )
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        if self.options.with_ssl:
            self.requires("openssl/1.1.1q")
        if self.options.with_postgresql:
            self.requires("libpq/14.2")
        if self.options.with_mysql:
            self.requires("libmysqlclient/8.0.29")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("{}-{}".format(self.name, self.version), self.source_folder)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        yes_no = lambda v: "yes" if v else "no"
        configure_args = [
            "--enable-shared={}".format(yes_no(self.options.shared)),
            "--enable-static={}".format(yes_no(not self.options.shared)),
            "--with-pic={}".format(yes_no(self.options.get_safe("fPIC", True))),
        ]

        # These options do not support yes/no
        if self.options.with_ssl:
            configure_args.append("--with-ssl")
        if self.options.with_mysql:
            configure_args.append("--with-mysql")
        if self.options.with_postgresql:
            configure_args.append("--with-postgresql")

        self._autotools.configure(configure_dir=self.source_folder, args=configure_args)
        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = self._configure_autotools()
        autotools.install()
        rmdir(self, os.path.join(os.path.join(self.package_folder, "share")))
        rm(self, "*.la", os.path.join(self.package_folder), recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["resip", "rutil", "dum", "resipares"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["pthread"]
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
