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
import glob
import os
import re


class PremakeConan(ConanFile):
    name = "premake"
    topics = ("build", "build-systems")
    description = "Describe your software project just once, using Premake's simple and easy to read syntax, and build it everywhere"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://premake.github.io"
    license = "BSD-3-Clause"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "lto": [True, False],
    }
    default_options = {
        "lto": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def config_options(self):
        if self.settings.os != "Windows" or self.settings.compiler == "Visual Studio":
            self.options.rm_safe("lto")

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self, skip_x64_x86=True):
            raise ConanInvalidConfiguration("Cross-building not implemented")

    @property
    def _msvc_version(self):
        return {
            "12": "2013",
            "14": "2015",
            "15": "2017",
            "16": "2019",
        }.get(str(self.settings.compiler.version), "2017")

    @property
    def _msvc_build_dirname(self):
        return "vs{}".format(self._msvc_version)

    def _version_info(self, version):
        res = []
        for p in re.split("[.-]|(alpha|beta)", version):
            if p is None:
                continue
            try:
                res.append(int(p))
                continue
            except ValueError:
                res.append(p)
        return tuple(res)

    @property
    def _gmake_directory_name_prefix(self):
        if self._version_info(self.version) <= self._version_info("5.0.0-alpha14"):
            return "gmake"
        else:
            return "gmake2"

    @property
    def _gmake_platform(self):
        return {
            "FreeBSD": "bsd",
            "Windows": "windows",
            "Linux": "unix",
            "Macos": "macosx",
        }[str(self.settings.os)]

    @property
    def _gmake_build_dirname(self):
        return "{}.{}".format(self._gmake_directory_name_prefix, self._gmake_platform)

    @property
    def _gmake_config(self):
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        if self.settings.os == "Windows":
            arch = {
                "x86": "x86",
                "x86_64": "x64",
            }[str(self.settings.arch)]
            config = "{}_{}".format(build_type, arch)
        else:
            config = build_type
        return config

    def _patch_sources(self):
        apply_conandata_patches(self)
        if self.options.get_safe("lto", None) == False:
            for fn in glob.glob(
                os.path.join(self.source_folder, "build", self._gmake_build_dirname, "*.make")
            ):
                replace_in_file(self, fn, "-flto", "", strict=False)

    def build(self):
        self._patch_sources()
        if self.settings.compiler == "Visual Studio":
            with chdir(self, os.path.join(self.source_folder, "build", self._msvc_build_dirname)):
                msbuild = MSBuild(self)
                msbuild.build(
                    "Premake5.sln",
                    platforms={
                        "x86": "Win32",
                        "x86_64": "x64",
                    },
                )
        else:
            with chdir(self, os.path.join(self.source_folder, "build", self._gmake_build_dirname)):
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make(target="Premake5", args=["verbose=1", "config={}".format(self._gmake_config)])

    def package(self):
        copy(self, pattern="LICENSE.txt", dst="licenses", src=self.source_folder)
        copy(self, pattern="*premake5.exe", dst="bin", keep_path=False)
        copy(self, pattern="*premake5", dst="bin", keep_path=False)

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
