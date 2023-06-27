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
from conan.tools.scm import Version
from conan.tools.system import package_manager
import contextlib
import os

required_conan_version = ">=1.33.0"


class GfCompleteConan(ConanFile):
    name = "gf-complete"
    description = "A library for Galois Field arithmetic"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ceph/gf-complete"
    license = "BSD-3-Clause"
    topics = ("galois field", "math", "algorithms")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "neon": [True, False, "auto"],
        "sse": [True, False, "auto"],
        "avx": [True, False, "auto"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "neon": "auto",
        "sse": "auto",
        "avx": "auto",
    }

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:
            self.options.rm_safe("sse")
            self.options.rm_safe("avx")
        if "arm" not in self.settings.arch:
            self.options.rm_safe("neon")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        if is_msvc(self):
            self.requires("getopt-for-visual-studio/20200201")

    def validate(self):
        if is_msvc(self):
            if self.options.shared:
                raise ConanInvalidConfiguration("gf-complete doesn't support shared with Visual Studio")
            if self.version == "1.03":
                raise ConanInvalidConfiguration("gf-complete 1.03 doesn't support Visual Studio")

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Don't build tests and examples (and also tools if Visual Studio)
        to_build = ["src"]
        if not is_msvc(self):
            to_build.append("tools")
        replace_in_file(
            self,
            os.path.join(self.source_folder, "Makefile.am"),
            "SUBDIRS = src tools test examples",
            "SUBDIRS = {}".format(" ".join(to_build)),
        )
        # Honor build type settings and fPIC option
        for subdir in ["src", "tools"]:
            for flag in ["-O3", "-fPIC"]:
                replace_in_file(self, os.path.join(self.source_folder, subdir, "Makefile.am"), flag, "")

    @contextlib.contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self):
                env = {
                    "CC": "{} cl -nologo".format(unix_path(self.deps_user_info["automake"].compile)),
                    "CXX": "{} cl -nologo".format(unix_path(self.deps_user_info["automake"].compile)),
                    "LD": "{} link -nologo".format(unix_path(self.deps_user_info["automake"].compile)),
                    "AR": "{} lib".format(unix_path(self.deps_user_info["automake"].ar_lib)),
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        self._autotools.libs = []
        if is_msvc(self):
            self._autotools.flags.append("-FS")
        elif "x86" in self.settings.arch:
            self._autotools.flags.append("-mstackrealign")

        yes_no = lambda v: "yes" if v else "no"
        conf_args = [
            "--enable-shared={}".format(yes_no(self.options.shared)),
            "--enable-static={}".format(yes_no(not self.options.shared)),
        ]

        if "arm" in self.settings.arch:
            if self.options.neon != "auto":
                conf_args.append("--enable-neon={}".format(yes_no(self.options.neon)))

        if self.settings.arch in ["x86", "x86_64"]:
            if self.options.sse != "auto":
                conf_args.append("--enable-sse={}".format(yes_no(self.options.sse)))

            if self.options.avx != "auto":
                conf_args.append("--enable-avx={}".format(yes_no(self.options.avx)))

        self._autotools.configure(args=conf_args, configure_dir=self.source_folder)

        return self._autotools

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")), win_bash=tools.os_info.is_windows)
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["gf_complete"]

        if not is_msvc(self):
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info("Appending PATH environment variable: {}".format(bin_path))
            self.env_info.PATH.append(bin_path)
