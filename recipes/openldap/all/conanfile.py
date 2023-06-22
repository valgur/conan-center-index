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

required_conan_version = ">=1.43.0"


class OpenldapConan(ConanFile):
    name = "openldap"
    description = "OpenLDAP C++ library"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.openldap.org/"
    license = "OLDAP-2.8"
    topics = ("ldap", "load-balancer", "directory-access")
    exports_sources = ["patches/*"]
    settings = settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cyrus_sasl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cyrus_sasl": True,
    }
    _autotools = None
    _configure_vars = None

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def requirements(self):
        self.requires("openssl/1.1.1q")
        if self.options.with_cyrus_sasl:
            self.requires("cyrus-sasl/2.1.27")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.name} is only supported on Linux")

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        def yes_no(v):
            return "yes" if v else "no"

        self._autotools = AutoToolsBuildEnvironment(self)
        configure_args = [
            "--enable-shared={}".format(yes_no(self.options.shared)),
            "--enable-static={}".format(yes_no(not self.options.shared)),
            "--with-cyrus_sasl={}".format(yes_no(self.options.with_cyrus_sasl)),
            "--with-pic={}".format(yes_no(self.options.get_safe("fPIC", True))),
            "--without-fetch",
            "--with-tls=openssl",
            "--enable-auditlog",
        ]
        self._configure_vars = self._autotools.vars
        self._configure_vars["systemdsystemunitdir"] = os.path.join(self.package_folder, "res")

        # Need to link to -pthread instead of -lpthread for gcc 8 shared=True
        # on CI job. Otherwise, linking fails.
        self._autotools.libs.remove("pthread")
        self._configure_vars["LIBS"] = self._configure_vars["LIBS"].replace("-lpthread", "-pthread")

        self._autotools.configure(
            args=configure_args, configure_dir=self.source_folder, vars=self._configure_vars
        )
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        autotools = self._configure_autotools()

        autotools.make(vars=self._configure_vars)

    def package(self):
        autotools = self._configure_autotools()
        autotools.install(vars=self._configure_vars)
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)
        copy(self, "COPYRIGHT", dst="licenses", src=self.source_folder)
        for folder in ["var", "share", "etc", "lib/pkgconfig", "res"]:
            rmdir(self, os.path.join(self.package_folder, folder))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.env_info.PATH.append(bin_path)
        self.output.info("Appending PATH environment variable: {}".format(bin_path))

        self.cpp_info.libs = ["ldap", "lber"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
