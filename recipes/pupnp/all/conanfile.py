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
import os

required_conan_version = ">=1.33.0"


class PupnpConan(ConanFile):
    name = "pupnp"
    description = (
        "The portable Universal Plug and Play (UPnP) SDK "
        "provides support for building UPnP-compliant control points, "
        "devices, and bridges on several operating systems."
    )
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/pupnp/pupnp"
    topics = ("upnp", "networking")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "ipv6": [True, False],
        "reuseaddr": [True, False],
        "webserver": [True, False],
        "client": [True, False],
        "device": [True, False],
        "largefile": [True, False],
        "tools": [True, False],
        "blocking-tcp": [True, False],
        "debug": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "ipv6": True,
        "reuseaddr": True,
        "webserver": True,
        "client": True,
        "device": True,
        "largefile": True,
        "tools": True,
        "blocking-tcp": False,
        "debug": True,  # Actually enables logging routines...
    }

    _autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            # Note, pupnp has build instructions for Visual Studio but they
            # include VC 6 and require pthreads-w32 library.
            # Someone who needs it and has possibility to build it could step in.
            raise ConanInvalidConfiguration("Visual Studio not supported yet in this recipe")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")
        self.build_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                "--enable-static=%s" % ("no" if self.options.shared else "yes"),
                "--enable-shared=%s" % ("yes" if self.options.shared else "no"),
                "--disable-samples",
            ]

            def enable_disable(opt):
                what = "enable" if getattr(self.options, opt) else "disable"
                return "--{}-{}".format(what, opt)

            args.extend(
                map(
                    enable_disable,
                    ("ipv6", "reuseaddr", "webserver", "client", "device", "largefile", "tools", "debug"),
                )
            )

            args.append(
                "--%s-blocking_tcp_connections"
                % ("enable" if getattr(self.options, "blocking-tcp") else "disable")
            )

            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.configure(configure_dir=self.source_folder, args=args)
        return self._autotools

    def build(self):
        with chdir(self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")), win_bash=tools.os_info.is_windows)
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        autotools = self._configure_autotools()
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "libupnp"
        self.cpp_info.libs = ["upnp", "ixml"]
        self.cpp_info.includedirs.append(os.path.join("include", "upnp"))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread"])
            self.cpp_info.cflags.extend(["-pthread"])
            self.cpp_info.cxxflags.extend(["-pthread"])
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["iphlpapi", "ws2_32"])
