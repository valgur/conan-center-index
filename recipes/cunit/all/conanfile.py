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
from contextlib import contextmanager
import glob
import os

required_conan_version = ">=1.33.0"


class CunitConan(ConanFile):
    name = "cunit"
    description = "A Unit Testing Framework for C"
    topics = "testing"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://cunit.sourceforge.net/"
    license = "BSD-3-Clause"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_automated": [True, False],
        "enable_basic": [True, False],
        "enable_console": [True, False],
        "with_curses": [False, "ncurses"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_automated": True,
        "enable_basic": True,
        "enable_console": True,
        "with_curses": False,
    }

    _autotools = None

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        if self.options.with_curses == "ncurses":
            self.requires("ncurses/6.2")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        with chdir(self.source_folder):
            for f in glob.glob("*.c"):
                os.chmod(f, 0o644)

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    @contextmanager
    def _build_context(self):
        env = {}
        if self.settings.compiler == "Visual Studio":
            with vcvars(self.settings):
                env.update(
                    {
                        "AR": "{} lib".format(unix_path(self._user_info_build["automake"].ar_lib)),
                        "CC": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                        "CXX": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                        "NM": "dumpbin -symbols",
                        "OBJDUMP": ":",
                        "RANLIB": ":",
                        "STRIP": ":",
                    }
                )
                with environment_append(self, env):
                    yield
        else:
            with environment_append(self, env):
                yield

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        self._autotools.libs = []
        host, build = None, None
        if self.settings.compiler == "Visual Studio":
            self._autotools.flags.append("-FS")
            # MSVC canonical names aren't understood
            host, build = False, False
        conf_args = [
            "--datarootdir={}".format(os.path.join(self.package_folder, "bin", "share").replace("\\", "/")),
            "--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug",
            "--enable-automated" if self.options.enable_automated else "--disable-automated",
            "--enable-basic" if self.options.enable_basic else "--disable-basic",
            "--enable-console" if self.options.enable_console else "--disable-console",
            "--enable-curses" if self.options.with_curses != False else "--disable-curses",
        ]
        if self.options.shared:
            conf_args.extend(["--enable-shared", "--disable-static"])
        else:
            conf_args.extend(["--disable-shared", "--enable-static"])
        self._autotools.configure(args=conf_args, host=host, build=build)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        with self._build_context():
            with chdir(self.source_folder):
                self.run("{} -fiv".format(get_env(self, "AUTORECONF")), win_bash=tools.os_info.is_windows)
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst="licenses")
        with self._build_context():
            with chdir(self.source_folder):
                autotools = self._configure_autotools()
                autotools.install()

        if self.settings.compiler == "Visual Studio" and self.options.shared:
            rename(
                self,
                os.path.join(self.package_folder, "lib", "cunit.dll.lib"),
                os.path.join(self.package_folder, "lib", "cunit.lib"),
            )

        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "bin", "share", "man"))
        rmdir(self, os.path.join(self.package_folder, "doc"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "CUnit"
        self.cpp_info.names["cmake_find_package_multi"] = "CUnit"
        self.cpp_info.libs = ["cunit"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("CU_DLL")
