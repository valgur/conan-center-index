import os
import shutil

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rename, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import check_min_vs, is_msvc, msvc_runtime_flag

required_conan_version = ">=1.57.0"


class CoinOsiConan(ConanFile):
    name = "coin-osi"
    description = "COIN-OR Linear Programming Solver"
    topics = ("clp", "simplex", "solver", "linear", "programming")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/coin-or/Osi"
    license = "EPL-2.0"
    package_type = "library"
    settings = "os", "arch", "build_type", "compiler"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_glpk": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_glpk": True,
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
        self.requires("coin-utils/2.11.11")
        self.requires("openblas/0.3.27")
        if self.options.with_glpk:
            self.requires("glpk/4.48")
        # TODO: add support for: Cplex, Mosek, Xpress, Gurobi
        # https://github.com/coin-or/Osi/blob/stable/0.108/Osi/configure.ac#L65-L77
        # soplex support requires v4.0, which is not available on CCI and is distributed under ZIB Academic License
        # https://github.com/coin-or-tools/ThirdParty-SoPlex/blob/master/INSTALL.SoPlex

    def build_requirements(self):
        self.tool_requires("coin-buildtools/0.8.11")
        self.tool_requires("gnu-config/cci.20210814")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()

        deps = PkgConfigDeps(self)
        deps.generate()

        def _add_pkg_config_alias(src_name, dst_name):
            shutil.copy(os.path.join(self.generators_folder, f"{src_name}.pc"),
                        os.path.join(self.generators_folder, f"{dst_name}.pc"))

        _add_pkg_config_alias("openblas", "coinblas")
        _add_pkg_config_alias("openblas", "coinlapack")
        if self.options.with_glpk:
            _add_pkg_config_alias("glpk", "coinglpk")

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            # the coin*.pc pkg-config files are only used when set to BUILD
            "--with-blas=BUILD",
            "--with-lapack=BUILD",
            "--with-glpk=BUILD" if self.options.with_glpk else "--without-glpk",
            "--with-soplex=no",
            # These are only used for sample datasets
            "--without-netlib",
            "--without-sample",
            "--disable-dependency-linking",
            "F77=unavailable",
        ])
        if is_msvc(self):
            tc.extra_cxxflags.append("-EHsc")
            tc.configure_args.append(f"--enable-msvc={msvc_runtime_flag(self)}")
            if check_min_vs(self, "180", raise_invalid=False):
                tc.extra_cflags.append("-FS")
                tc.extra_cxxflags.append("-FS")
        env = tc.environment()
        if is_msvc(self):
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", "lib -nologo")
        if self._settings_build.os == "Windows":
            # TODO: Something to fix in conan client or pkgconf recipe?
            # This is a weird workaround when build machine is Windows. Here we have to inject regular
            # Windows path to pc files folder instead of unix path flavor injected by AutotoolsToolchain...
            env.define("PKG_CONFIG_PATH", self.generators_folder)
        tc.generate(env)

    def build(self):
        apply_conandata_patches(self)
        copy(self, "*", os.path.join(self.dependencies.build["coin-buildtools"].package_folder, "res"),
             os.path.join(self.source_folder, "BuildTools"))
        copy(self, "*", os.path.join(self.dependencies.build["coin-buildtools"].package_folder, "res"),
             os.path.join(self.source_folder, "Osi", "BuildTools"))
        for gnu_config in [
            self.conf.get("user.gnu-config:config_guess", check_type=str),
            self.conf.get("user.gnu-config:config_sub", check_type=str),
        ]:
            copy(self, os.path.basename(gnu_config), src=os.path.dirname(gnu_config), dst=self.source_folder)
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install(args=["-j1"])
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)
        if is_msvc(self):
            for l in ("Osi", "OsiCommonTests"):
                rename(self, os.path.join(self.package_folder, "lib", f"lib{l}.lib"),
                             os.path.join(self.package_folder, "lib", f"{l}.lib"))

    def package_info(self):
        self.cpp_info.components["libosi"].set_property("pkg_config_name", "osi")
        self.cpp_info.components["libosi"].libs = ["Osi"]
        self.cpp_info.components["libosi"].includedirs = [os.path.join("include", "coin")]
        self.cpp_info.components["libosi"].requires = ["coin-utils::coin-utils", "openblas::openblas"]

        self.cpp_info.components["osi-unittests"].set_property("pkg_config_name", "osi-unittests")
        self.cpp_info.components["osi-unittests"].libs = ["OsiCommonTests"]
        self.cpp_info.components["osi-unittests"].requires = ["libosi"]

        if self.options.with_glpk:
            self.cpp_info.components["osi-glpk"].set_property("pkg_config_name", "osi-glpk")
            self.cpp_info.components["osi-glpk"].libs = ["OsiGlpk"]
            self.cpp_info.components["osi-glpk"].requires = ["libosi", "glpk::glpk"]
