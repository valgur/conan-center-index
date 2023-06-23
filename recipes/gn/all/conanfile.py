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
import conan.tools.files as tools_files
import conan.tools.scm as tools_scm
import os
import sys
import textwrap
import time

required_conan_version = ">=1.46.0"


class GnConan(ConanFile):
    name = "gn"
    description = "GN is a meta-build system that generates build files for Ninja."
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("build", "system", "ninja")
    license = "BSD-3-Clause"
    homepage = "https://gn.googlesource.com/"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _minimum_compiler_version_supporting_cxx17(self):
        return {"Visual Studio": 15, "gcc": 7, "clang": 4, "apple-clang": 10}.get(str(self.settings.compiler))

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 17)
        else:
            if self._minimum_compiler_version_supporting_cxx17:
                if (
                    tools_scm.Version(self.settings.compiler.version)
                    < self._minimum_compiler_version_supporting_cxx17
                ):
                    raise ConanInvalidConfiguration("gn requires a compiler supporting c++17")
            else:
                self.output.warn(
                    "gn recipe does not recognize the compiler. gn requires a compiler supporting c++17. Assuming it does."
                )

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        tools_files.get(self, **self.conan_data["sources"][self.version], destination=self.source_folder)

    def build_requirements(self):
        # FIXME: add cpython build requirements for `build/gen.py`.
        self.build_requires("ninja/1.10.2")

    @contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self.settings):
                yield
        else:
            compiler_defaults = {}
            if self.settings.compiler == "gcc":
                compiler_defaults = {
                    "CC": "gcc",
                    "CXX": "g++",
                    "AR": "ar",
                    "LD": "g++",
                }
            elif self.settings.compiler == "clang":
                compiler_defaults = {
                    "CC": "clang",
                    "CXX": "clang++",
                    "AR": "ar",
                    "LD": "clang++",
                }
            env = {}
            for k in ("CC", "CXX", "AR", "LD"):
                v = get_env(self, k, compiler_defaults.get(k, None))
                if v:
                    env[k] = v
            with environment_append(self, env):
                yield

    @staticmethod
    def _to_gn_platform(os_, compiler):
        if is_apple_os(self, os_):
            return "darwin"
        if compiler == "Visual Studio":
            return "msvc"
        # Assume gn knows about the os
        return str(os_).lower()

    def build(self):
        with chdir(self, self.source_folder):
            with self._build_context():
                # Generate dummy header to be able to run `build/ben.py` with `--no-last-commit-position`. This allows running the script without the tree having to be a git checkout.
                save(
                    self,
                    os.path.join("src", "gn", "last_commit_position.h"),
                    textwrap.dedent(
                        """\
                                #pragma once
                                #define LAST_COMMIT_POSITION "1"
                                #define LAST_COMMIT_POSITION_NUM 1
                                """
                    ),
                )
                conf_args = [
                    "--no-last-commit-position",
                    "--host={}".format(self._to_gn_platform(self.settings.os, self.settings.compiler)),
                ]
                if self.settings.build_type == "Debug":
                    conf_args.append("-d")
                self.run(
                    "{} build/gen.py {}".format(sys.executable, " ".join(conf_args)), run_environment=True
                )
                # Try sleeping one second to avoid time skew of the generated ninja.build file (and having to re-run build/gen.py)
                time.sleep(1)
                build_args = [
                    "-C",
                    "out",
                    "-j{}".format(cpu_count(self)),
                ]
                self.run("ninja {}".format(" ".join(build_args)), run_environment=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(
            self,
            "gn",
            src=os.path.join(self.source_folder, "out"),
            dst=os.path.join(self.package_folder, "bin"),
        )
        copy(
            self,
            "gn.exe",
            src=os.path.join(self.source_folder, "out"),
            dst=os.path.join(self.package_folder, "bin"),
        )

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
        self.cpp_info.includedirs = []
