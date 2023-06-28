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

required_conan_version = ">=1.53.0"


class CoinCbcConan(ConanFile):
    name = "coin-cbc"
    description = "COIN-OR Branch-and-Cut solver"
    license = ("EPL-2.0",)
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/coin-or/Clp"
    topics = ("clp", "simplex", "solver", "linear", "programming")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
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

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("coin-utils/2.11.4")
        self.requires("coin-osi/0.108.6")
        self.requires("coin-clp/1.17.6")
        self.requires("coin-cgl/0.60.3")
        if is_msvc(self) and self.options.parallel:
            self.requires("pthreads4w/3.0.0")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("coin-cbc does not support shared builds on Windows")
        # FIXME: This issue likely comes from very old autotools versions used to produce configure.
        if hasattr(self, "settings_build") and cross_building(self) and self.options.shared:
            raise ConanInvalidConfiguration("coin-cbc shared not supported yet when cross-building")

    def build_requirements(self):
        self.tool_requires("gnu-config/cci.20201022")
        self.tool_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.tool_requires("msys2/cci.latest")
        if is_msvc(self):
            self.tool_requires("automake/1.16.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self.settings):
                env = {
                    "CC": "{} cl -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile-wrapper"))
                    ),
                    "CXX": "{} cl -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile-wrapper"))
                    ),
                    "LD": "{} link -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile-wrapper"))
                    ),
                    "AR": "{} lib".format(unix_path(self, self.conf_info.get("user.automake:lib-wrapper"))),
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def generate(self):
        tc = AutotoolsToolchain(self)
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--enable-cbc-parallel={}".format(yes_no(self.options.parallel)),
            "--without-blas",
            "--without-lapack",
        ]
        if is_msvc(self):
            tc.cxxflags.append("-EHsc")
            tc.configure_args.append(f"--enable-msvc={self.settings.compiler.runtime}")
            if Version(self.settings.compiler.version) >= 12:
                tc.cxxflags.append("-FS")
            if self.options.parallel:
                pthreads_path = os.path.join(
                    self.dependencies["pthreads4w"].cpp_info.libdirs[0],
                    self.dependencies["pthreads4w"].cpp_info.libs[0] + ".lib",
                )
                tc.configure_args.append("--with-pthreadsw32-lib={}".format(unix_path(self, pthreads_path)))
                tc.configure_args.append(
                    "--with-pthreadsw32-incdir={}".format(
                        unix_path(self, self.dependencies["pthreads4w"].cpp_info.includedirs[0])
                    )
                )
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        shutil.copy(
            self.conf_info.get("user.gnu-config:CONFIG_SUB"), os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self.conf_info.get("user.gnu-config:CONFIG_GUESS"),
            os.path.join(self.source_folder, "config.guess"),
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
            if is_msvc(self):
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
        self.cpp_info.components["libcbc"].set_property("pkg_config_name", "cbc")
        if self.settings.os in ["Linux", "FreeBSD"] and self.options.parallel:
            self.cpp_info.components["libcbc"].system_libs.append("pthread")
        if self.settings.os in ["Windows"] and self.options.parallel:
            self.cpp_info.components["libcbc"].requires.append("pthreads4w::pthreads4w")

        self.cpp_info.components["osi-cbc"].libs = ["OsiCbc"]
        self.cpp_info.components["osi-cbc"].requires = ["libcbc"]
        self.cpp_info.components["osi-cbc"].set_property("pkg_config_name", "osi-cbc")

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
