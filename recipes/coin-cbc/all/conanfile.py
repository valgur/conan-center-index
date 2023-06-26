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
from contextlib import contextmanager
import os
import shutil

required_conan_version = ">=1.47.0"


class CoinCbcConan(ConanFile):
    name = "coin-cbc"
    description = "COIN-OR Branch-and-Cut solver"
    topics = ("clp", "simplex", "solver", "linear", "programming")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/coin-or/Clp"
    license = ("EPL-2.0",)
    settings = "os", "arch", "build_type", "compiler"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "parallel": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "parallel": False,
    }
    generators = "pkg_config"

    _autotools = None

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("coin-utils/2.11.4")
        self.requires("coin-osi/0.108.6")
        self.requires("coin-clp/1.17.6")
        self.requires("coin-cgl/0.60.3")
        if self.settings.compiler == "Visual Studio" and self.options.parallel:
            self.requires("pthreads4w/3.0.0")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    def build_requirements(self):
        self.tool_requires("gnu-config/cci.20201022")
        self.tool_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.tool_requires("msys2/cci.latest")
        if self.settings.compiler == "Visual Studio":
            self.tool_requires("automake/1.16.5")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("coin-cbc does not support shared builds on Windows")
        # FIXME: This issue likely comes from very old autotools versions used to produce configure.
        if hasattr(self, "settings_build") and cross_building(self) and self.options.shared:
            raise ConanInvalidConfiguration("coin-cbc shared not supported yet when cross-building")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self.settings):
                env = {
                    "CC": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                    "CXX": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                    "LD": "{} link -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                    "AR": "{} lib".format(unix_path(self._user_info_build["automake"].ar_lib)),
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
        yes_no = lambda v: "yes" if v else "no"
        configure_args = [
            "--enable-shared={}".format(yes_no(self.options.shared)),
            "--enable-cbc-parallel={}".format(yes_no(self.options.parallel)),
            "--without-blas",
            "--without-lapack",
        ]
        if self.settings.compiler == "Visual Studio":
            self._autotools.cxx_flags.append("-EHsc")
            configure_args.append(f"--enable-msvc={self.settings.compiler.runtime}")
            if Version(self.settings.compiler.version) >= 12:
                self._autotools.flags.append("-FS")
            if self.options.parallel:
                configure_args.append(
                    "--with-pthreadsw32-lib={}".format(
                        unix_path(
                            self,
                            os.path.join(
                                self.dependencies["pthreads4w"].cpp_info.libdirs[0],
                                self.dependencies["pthreads4w"].cpp_info.libs[0] + ".lib",
                            ),
                        )
                    )
                )
                configure_args.append(
                    "--with-pthreadsw32-incdir={}".format(
                        unix_path(self.dependencies["pthreads4w"].cpp_info.includedirs[0])
                    )
                )
        self._autotools.configure(configure_dir=self.source_folder, args=configure_args)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_SUB, os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_GUESS, os.path.join(self.source_folder, "config.guess")
        )
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        # Installation script expects include/coin to already exist
        mkdir(self, os.path.join(self.package_folder, "include", "coin"))
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

        for l in ("CbcSolver", "Cbc", "OsiCbc"):
            os.unlink(f"{self.package_folder}/lib/lib{l}.la")
            if self.settings.compiler == "Visual Studio":
                rename(self, f"{self.package_folder}/lib/lib{l}.a", f"{self.package_folder}/lib/{l}.lib")

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.components["libcbc"].libs = ["CbcSolver", "Cbc"]
        self.cpp_info.components["libcbc"].includedirs.append(os.path.join("include", "coin"))
        self.cpp_info.components["libcbc"].requires = [
            "coin-clp::osi-clp",
            "coin-utils::coin-utils",
            "coin-osi::coin-osi",
            "coin-cgl::coin-cgl",
        ]
        self.cpp_info.components["libcbc"].names["pkg_config"] = "cbc"
        if self.settings.os in ["Linux", "FreeBSD"] and self.options.parallel:
            self.cpp_info.components["libcbc"].system_libs.append("pthread")
        if self.settings.os in ["Windows"] and self.options.parallel:
            self.cpp_info.components["libcbc"].requires.append("pthreads4w::pthreads4w")

        self.cpp_info.components["osi-cbc"].libs = ["OsiCbc"]
        self.cpp_info.components["osi-cbc"].requires = ["libcbc"]
        self.cpp_info.components["osi-cbc"].names["pkg_config"] = "osi-cbc"

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
