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
from conan.errors import ConanInvalidConfiguration
from contextlib import contextmanager
import os
import shutil

required_conan_version = ">=1.47.0"


class VerilatorConan(ConanFile):
    name = "verilator"
    description = (
        "Verilator compiles synthesizable Verilog and Synthesis assertions into single- or multithreaded C++"
        " or SystemC code"
    )
    license = "LGPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.veripool.org/wiki/verilator"
    topics = ("verilog", "hdl", "eda", "simulator", "hardware", "fpga", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os == "Windows":
            self.requires("strawberryperl/5.30.0.1")
        if is_msvc(self):
            self.requires("dirent/1.23.2", private=True)

    def package_id(self):
        # Verilator is a executable-only package, so the compiler version does not matter
        del self.info.settings.compiler.version

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration("Cross building is not yet supported. Contributions are welcome")

        if (
            Version(self.version) >= "4.200"
            and self.settings.compiler == "gcc"
            and Version(self.settings.compiler.version) < "7"
        ):
            raise ConanInvalidConfiguration("GCC < version 7 is not supported")

        if self.settings.os == "Windows" and Version(self.version) >= "4.200":
            raise ConanInvalidConfiguration("Windows build is not yet supported. Contributions are welcome")

    @property
    def _needs_old_bison(self):
        return Version(self.version) < "4.100"

    def build_requirements(self):
        if self._settings_build.os == "Windows" and "CONAN_BASH_PATH" not in os.environ:
            if is_msvc(self):
                self.build_requires("msys2/cci.latest")
                self.build_requires("automake/1.16.4")
            if self._needs_old_bison:
                # don't upgrade to bison 3.7.0 or above, or it fails to build
                # because of https://github.com/verilator/verilator/pull/2505
                self.build_requires("winflexbison/2.5.22")
            else:
                self.build_requires("winflexbison/2.5.24")
            self.build_requires("strawberryperl/5.30.0.1")
        else:
            self.build_requires("flex/2.6.4")
            if self._needs_old_bison:
                # don't upgrade to bison 3.7.0 or above, or it fails to build
                # because of https://github.com/verilator/verilator/pull/2505
                self.build_requires("bison/3.5.3")
            else:
                self.build_requires("bison/3.7.6")
        if Version(self.version) >= "4.224":
            self.build_requires("autoconf/2.71")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @contextmanager
    def _build_context(self):
        if is_msvc(self):
            build_env = {
                "CC": "{} cl -nologo".format(unix_path(self, self.conf_info.get("user.automake:compile"))),
                "CXX": "{} cl -nologo".format(unix_path(self, self.conf_info.get("user.automake:compile"))),
                "AR": "{} lib".format(unix_path(self, self.conf_info.get("user.automake:ar_lib"))),
            }
            with vcvars(self.settings):
                with environment_append(self, build_env):
                    yield
        else:
            yield

    def generate(self):
        tc = AutotoolsToolchain(self)
        if self.settings.get_safe("compiler.libcxx") == "libc++":
            tc.libs.append("c++")
        if is_msvc(self):
            tc.cxxflags.append("-EHsc")
            tc.defines.append("YY_NO_UNISTD_H")
            tc.cxxflags.append("-FS")
        tc.configure_args += ["--datarootdir={}/bin/share".format(unix_path(self, self.package_folder))]
        yacc = get_env(self, "YACC")
        if yacc:
            if yacc.endswith(" -y"):
                yacc = yacc[:-3]
        tc.generate()

    @property
    def _make_args(self):
        args = [
            "CFG_WITH_DEFENV=false",
            "SRC_TARGET={}".format("dbg" if self.settings.build_type == "Debug" else "opt"),
        ]
        if self.settings.build_type == "Debug":
            args.append("DEBUG=1")
        if is_msvc(self):
            args.append(
                "PROGLINK={}".format(
                    unix_path(self, os.path.join(self.build_folder, self.source_folder, "msvc_link.sh"))
                )
            )
        return args

    def _patch_sources(self):
        if Version(self.version) < "4.200":
            apply_conandata_patches(self)
        try:
            os.unlink(os.path.join(self.source_folder, "src", "config_build.h"))
        except FileNotFoundError:
            pass

        if is_msvc(self):
            replace_in_file(
                self, os.path.join(self.source_folder, "src", "Makefile_obj.in"), "${LINK}", "${PROGLINK}"
            )

    def build(self):
        self._patch_sources()
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make(args=self._make_args)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.install(args=self._make_args)

        rmdir(self, os.path.join(self.package_folder, "bin", "share", "man"))
        rmdir(self, os.path.join(self.package_folder, "bin", "share", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "bin", "share", "verilator", "examples"))
        os.unlink(
            os.path.join(self.package_folder, "bin", "share", "verilator", "verilator-config-version.cmake")
        )
        rename(
            self,
            os.path.join(self.package_folder, "bin", "share", "verilator", "verilator-config.cmake"),
            os.path.join(self.package_folder, "bin", "share", "verilator", "verilator-tools.cmake"),
        )
        replace_in_file(
            self,
            os.path.join(self.package_folder, "bin", "share", "verilator", "verilator-tools.cmake"),
            "${CMAKE_CURRENT_LIST_DIR}",
            "${CMAKE_CURRENT_LIST_DIR}/../../..",
        )
        if self.settings.build_type == "Debug":
            replace_in_file(
                self,
                os.path.join(self.package_folder, "bin", "share", "verilator", "verilator-tools.cmake"),
                "verilator_bin",
                "verilator_bin_dbg",
            )

        shutil.move(
            os.path.join(self.package_folder, "bin", "share", "verilator", "include"),
            os.path.join(self.package_folder),
        )

        if Version(self.version) >= "4.224":
            shutil.move(
                os.path.join(
                    self.package_folder, "bin", "share", "verilator", "bin", "verilator_ccache_report"
                ),
                os.path.join(self.package_folder, "bin", "verilator_ccache_report"),
            )

        shutil.move(
            os.path.join(self.package_folder, "bin", "share", "verilator", "bin", "verilator_includer"),
            os.path.join(self.package_folder, "bin", "verilator_includer"),
        )

        rmdir(self, os.path.join(self.package_folder, "bin", "share", "verilator", "bin"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(bindir)

        verilator_bin = "verilator_bin_dbg" if self.settings.build_type == "Debug" else "verilator_bin"
        self.output.info(f"Setting VERILATOR_BIN environment variable to {verilator_bin}")
        self.env_info.VERILATOR_BIN = verilator_bin

        verilator_root = os.path.join(self.package_folder)
        self.output.info(f"Setting VERILATOR_ROOT environment variable to {verilator_root}")
        self.env_info.VERILATOR_ROOT = verilator_root

        self.cpp_info.builddirs.append(os.path.join("bin", "share", "verilator"))
        self.cpp_info.build_modules.append(os.path.join("bin", "share", "verilator", "verilator-tools.cmake"))
