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
import contextlib
import os
import textwrap

required_conan_version = ">=1.33.0"


class LzipConan(ConanFile):
    name = "lzip"
    description = (
        "Lzip is a lossless data compressor with a user interface similar to the one of gzip or bzip2"
    )
    topics = ("compressor", "lzma")
    license = "GPL-v2-or-later"
    homepage = "https://www.nongnu.org/lzip/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"

    exports_sources = "patches/**"

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not tools.get_env("CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Visual Studio is not supported")

    def package_id(self):
        del self.info.settings.compiler

    def _detect_compilers(self):
        tools.rmdir("detectdir")
        tools.mkdir("detectdir")
        with tools.chdir("detectdir"):
            tools.save(
                "CMakeLists.txt",
                textwrap.dedent(
                    """\
                cmake_minimum_required(VERSION 2.8)
                project(test C CXX)
                message(STATUS "CC=${CMAKE_C_COMPILER}")
                message(STATUS "CXX=${CMAKE_CXX_COMPILER}")
                file(WRITE cc.txt "${CMAKE_C_COMPILER}")
                file(WRITE cxx.txt "${CMAKE_CXX_COMPILER}")
                """
                ),
            )
            CMake(self).configure(source_folder="detectdir", build_folder="detectdir")
            cc = tools.load("cc.txt").strip()
            cxx = tools.load("cxx.txt").strip()
        return cc, cxx

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], destination=self._source_subfolder, strip_root=True
        )

    @contextlib.contextmanager
    def _build_context(self):
        env = {}
        cc, cxx = self._detect_compilers()
        if not tools.get_env("CC"):
            env["CC"] = cc
        if not tools.get_env("CXX"):
            env["CXX"] = cxx
        with tools.environment_append(env):
            yield

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        conf_args = []
        self._autotools.configure(args=conf_args, configure_dir=self._source_subfolder)
        return self._autotools

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        with self._build_context():
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses")
        with self._build_context():
            autotools = self._configure_autotools()
            with tools.environment_append(
                {
                    "CONAN_CPU_COUNT": "1",
                }
            ):
                autotools.install()

        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
