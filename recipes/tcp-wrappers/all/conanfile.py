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


class TcpWrappersConan(ConanFile):
    name = "tcp-wrappers"
    homepage = "ftp://ftp.porcupine.org/pub/security/index.html"
    description = "A security tool which acts as a wrapper for TCP daemons"
    topics = ("tcp", "ip", "daemon", "wrapper")
    url = "https://github.com/conan-io/conan-center-index"
    license = "BSD"
    exports_sources = "patches/**"
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
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Visual Studio is not supported")
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("tcp_wrappers_{}-ipv6.4".format(self.version), self.source_folder)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        with chdir(self.source_folder):
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
        copy(self, pattern="DISCLAIMER", src=self.source_folder, dst="licenses")

        for exe in ("safe_finger", "tcpd", "tcpdchk", "tcpdmatch", "try-from"):
            copy(self, exe, src=self.source_folder, dst="bin", keep_path=False)
        copy(self, "tcpd.h", src=self.source_folder, dst="include", keep_path=False)
        if self.options.shared:
            copy(self, "libwrap{}".format(self._shext), src=self.source_folder, dst="lib", keep_path=False)
        else:
            copy(self, "libwrap.a", src=self.source_folder, dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["wrap"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
