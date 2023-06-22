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
import shutil

required_conan_version = ">=1.33.0"


class LibId3TagConan(ConanFile):
    name = "libid3tag"
    description = "ID3 tag manipulation library."
    topics = ("mad", "id3", "MPEG", "audio", "decoder")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.underbit.com/products/mad/"
    license = "GPL-2.0-or-later"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    generator = "pkg_config", "visual_studio"

    _autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("zlib/1.2.11")

    def validate(self):
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration("libid3tag does not support shared library for MSVC")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        if not is_msvc(self):
            self.build_requires("gnu-config/cci.20201022")
            if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
                self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        if is_msvc(self):
            self._build_msvc()
        else:
            self._build_autotools()

    def _build_msvc(self):
        kwargs = {}
        with chdir(self, os.path.join(self.source_folder, "msvc++")):
            # cl : Command line error D8016: '/ZI' and '/Gy-' command-line options are incompatible
            replace_in_file(self, "libid3tag.dsp", "/ZI ", "")
            if self.settings.compiler == "clang":
                replace_in_file(self, "libid3tag.dsp", "CPP=cl.exe", "CPP=clang-cl.exe")
                replace_in_file(self, "libid3tag.dsp", "RSC=rc.exe", "RSC=llvm-rc.exe")
                kwargs["toolset"] = "ClangCl"
            if self.settings.arch == "x86_64":
                replace_in_file(self, "libid3tag.dsp", "Win32", "x64")
            with vcvars(self.settings):
                self.run("devenv /Upgrade libid3tag.dsp")
            msbuild = MSBuild(self)
            msbuild.build(project_file="libid3tag.vcxproj", **kwargs)

    def _configure_autotools(self):
        if not self._autotools:
            if self.options.shared:
                args = ["--disable-static", "--enable-shared"]
            else:
                args = ["--disable-shared", "--enable-static"]
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.configure(args=args, configure_dir=self.source_folder)
        return self._autotools

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    def _build_autotools(self):
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_SUB, os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_GUESS, os.path.join(self.source_folder, "config.guess")
        )
        autotools = self._configure_autotools()
        autotools.make()

    def _install_autotools(self):
        autotools = self._configure_autotools()
        autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)

    def package(self):
        copy(self, "COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "CREDITS", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if is_msvc(self):
            copy(
                self,
                pattern="*.lib",
                dst=os.path.join(self.package_folder, "lib"),
                src=self.source_folder,
                keep_path=False,
            )
            copy(
                self,
                pattern="id3tag.h",
                dst=os.path.join(self.package_folder, "include"),
                src=self.source_folder,
            )
        else:
            self._install_autotools()

    def package_info(self):
        self.cpp_info.libs = ["libid3tag" if is_msvc(self) else "id3tag"]
