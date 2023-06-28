# Warnings:
#   Disallowed attribute '_source_subfolder = 'source_subfolder''
#   Unexpected method '_datadir'
#   Unexpected method '_samplesdir'
#   Unexpected method '_make_args'
#   Unexpected method '_build_msvc'
#   Unexpected method '_configure_autotools'
#   Unexpected method '_build_autotools'
#   Unexpected method '_package_msvc'
#   Unexpected method '_package_autotools'

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
import os

required_conan_version = ">=1.47.0"


class Cc65Conan(ConanFile):
    name = "cc65"
    description = "A freeware C compiler for 6502 based systems"
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://cc65.github.io/"
    topics = ("compiler", "cmos", "6502", "8bit")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _datadir(self):
        return os.path.join(self.package_folder, "bin", "share", "cc65")

    @property
    def _samplesdir(self):
        return os.path.join(self.package_folder, "samples")

    @property
    def _make_args(self):
        datadir = self._datadir
        prefix = self.package_folder
        samplesdir = self._samplesdir
        if tools.os_info.is_windows:
            datadir = unix_path(self, datadir)
            prefix = unix_path(self, prefix)
            samplesdir = unix_path(self, samplesdir)
        args = [f"PREFIX={prefix}", f"datadir={datadir}", f"samplesdir={samplesdir}"]
        if self.settings.os == "Windows":
            args.append("EXE_SUFFIX=.exe")
        return args

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if is_msvc(self):
            if self.settings.arch not in ("x86", "x86_64"):
                raise ConanInvalidConfiguration("Invalid arch")
            if self.settings.arch == "x86_64":
                self.output.info("This recipe will build x86 instead of x86_64 (the binaries are compatible)")

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        if is_msvc(self):
            if self.settings.arch == "x86_64":
                self.info.settings.arch = "x86"

    def build_requirements(self):
        if is_msvc(self) and not which(self, "make"):
            self.build_requires("make/4.2.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _build_msvc(self):
        msbuild = MSBuild(self)
        msvc_platforms = {
            "x86": "Win32",
        }
        arch = str(self.settings.arch)
        if arch != "x86":
            self.output.warning("{} detected: building x86 instead".format(self.settings.arch))
            arch = "x86"

        msbuild.build(
            os.path.join(self.source_folder, "src", "cc65.sln"),
            build_type="Debug" if self.settings.build_type == "Debug" else "Release",
            arch=arch,
            platforms=msvc_platforms,
        )
        autotools = Autotools(self)
        autotools.configure()
        with chdir(self, os.path.join(self.source_folder, "libsrc")):
            autotools.make()

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.generate()
        return self._autotools

    def _build_autotools(self):
        autotools = Autotools(self)
        autotools.configure()
        with chdir(self, os.path.join(self.source_folder)):
            autotools.make(args=self._make_args)

    def _patch_sources(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            with chdir(self, os.path.join(self.source_folder, "src")):
                for fn in os.listdir("."):
                    if not fn.endswith(".vcxproj"):
                        continue
                    replace_in_file(self, fn, "v141", msvs_toolset(self))
                    replace_in_file(
                        self,
                        fn,
                        "<WindowsTargetPlatformVersion>10.0.16299.0</WindowsTargetPlatformVersion>",
                        "",
                    )
        if self.settings.os == "Windows":
            # Add ".exe" suffix to calls from cl65 to other utilities
            for fn, var in (
                ("cc65", "CC65"),
                ("ca65", "CA65"),
                ("co65", "CO65"),
                ("ld65", "LD65"),
                ("grc65", "GRC"),
            ):
                v = "{},".format(var).ljust(5)
                replace_in_file(
                    self,
                    os.path.join(self.source_folder, "src", "cl65", "main.c"),
                    'CmdInit (&{v} CmdPath, "{n}");'.format(v=v, n=fn),
                    'CmdInit (&{v} CmdPath, "{n}.exe");'.format(v=v, n=fn),
                )

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._build_msvc()
        else:
            self._build_autotools()

    def _package_msvc(self):
        copy(
            self,
            "*.exe",
            src=os.path.join(self.source_folder, "bin"),
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )
        for dir in ("asminc", "cfg", "include", "lib", "target"):
            copy(self, "*", src=os.path.join(self.source_folder, dir), dst=os.path.join(self._datadir, dir))

    def _package_autotools(self):
        autotools = Autotools(self)
        autotools.configure()
        with chdir(self, os.path.join(self.build_folder, self.source_folder)):
            autotools.install(args=self._make_args)

        rmdir(self._samplesdir)
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        if is_msvc(self):
            self._package_msvc()
        else:
            self._package_autotools()

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: %s" % bindir)
        self.env_info.PATH.append(bindir)

        self.output.info("Seting CC65_HOME environment variable: %s" % self._datadir)
        self.env_info.CC65_HOME = self._datadir

        bin_ext = ".exe" if self.settings.os == "Windows" else ""

        cc65_cc = os.path.join(bindir, "cc65" + bin_ext)
        self.output.info("Seting CC65 environment variable: {}".format(cc65_cc))
        self.env_info.CC65 = cc65_cc

        cc65_as = os.path.join(bindir, "ca65" + bin_ext)
        self.output.info("Seting AS65 environment variable: {}".format(cc65_as))
        self.env_info.AS65 = cc65_as

        cc65_ld = os.path.join(bindir, "cl65" + bin_ext)
        self.output.info("Seting LD65 environment variable: {}".format(cc65_ld))
        self.env_info.LD65 = cc65_ld
