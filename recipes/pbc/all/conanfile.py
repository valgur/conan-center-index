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


class PbcConan(ConanFile):
    name = "pbc"
    topics = ("crypto", "cryptography", "security", "pairings", "cryptographic")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://crypto.stanford.edu/pbc/"
    license = "LGPL-3.0"
    description = "The PBC (Pairing-Based Crypto) library is a C library providing low-level routines for pairing-based cryptosystems."

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    _autotools = None

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("gmp/6.2.1")

    def build_requirements(self):
        self.build_requires("bison/3.7.6")
        self.build_requires("flex/2.6.4")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        # Need to override environment or configure will fail despite that flex
        # is actually available.
        args = ["LEX=flex"]
        if self.options.shared:
            args.extend(["--disable-static", "--enable-shared"])
        else:
            args.extend(["--disable-shared", "--enable-static"])

        # No idea why this is necessary, but if you don't set CC this way, then
        # configure complains that it can't find gmp.
        if cross_building(self.settings) and self.settings.compiler == "apple-clang":
            xcr = XCRun(self.settings)
            target = to_apple_arch(self.settings.arch) + "-apple-darwin"

            min_ios = ""
            if self.settings.os == "iOS":
                min_ios = "-miphoneos-version-min={}".format(self.settings.os.version)

            args.append("CC={} -isysroot {} -target {} {}".format(xcr.cc, xcr.sdk_path, target, min_ios))

        self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"))
        autotools = self._configure_autotools()
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["pbc"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m"]
