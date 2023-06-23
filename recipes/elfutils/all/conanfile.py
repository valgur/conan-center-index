# TODO: verify the Conan v2 migration

import os
import glob

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
import glob

required_conan_version = ">=1.33.0"


class ElfutilsConan(ConanFile):
    name = "elfutils"
    description = "A dwarf, dwfl and dwelf functions to read DWARF, find separate debuginfo, symbols and inspect process state."
    homepage = "https://sourceware.org/elfutils"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("libelf", "libdw", "libasm")
    license = ["GPL-1.0-or-later", "LGPL-3.0-or-later", "GPL-2.0-or-later"]

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "debuginfod": [True, False],
        "libdebuginfod": [True, False],
        "with_bzlib": [True, False],
        "with_lzma": [True, False],
        "with_sqlite3": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "debuginfod": False,
        "libdebuginfod": False,
        "with_bzlib": True,
        "with_lzma": True,
        "with_sqlite3": False,
    }

    generators = "pkg_config"

    _autotools = None
    _source_subfolder = "source_subfolder"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "0.186":
            self.options.rm_safe("libdebuginfod")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def validate(self):
        if Version(self.version) >= "0.186":
            if self.settings.compiler in ["Visual Studio", "apple-clang", "msvc"]:
                raise ConanInvalidConfiguration(
                    "Compiler %s not supported. "
                    "elfutils only supports gcc and clang" % self.settings.compiler
                )
        else:
            if self.settings.compiler in ["Visual Studio", "clang", "apple-clang", "msvc"]:
                raise ConanInvalidConfiguration(
                    "Compiler %s not supported. " "elfutils only supports gcc" % self.settings.compiler
                )
        if self.settings.compiler != "gcc":
            self.output.warn("Compiler %s is not gcc." % self.settings.compiler)

    def requirements(self):
        self.requires("zlib/1.2.12")
        if self.options.with_sqlite3:
            self.requires("sqlite3/3.38.5")
        if self.options.with_bzlib:
            self.requires("bzip2/1.0.8")
        if self.options.with_lzma:
            self.requires("xz_utils/5.2.5")
        if self.options.get_safe("libdebuginfod"):
            self.requires("libcurl/7.83.0")
        if self.options.debuginfod:
            # FIXME: missing recipe for libmicrohttpd
            raise ConanInvalidConfiguration("libmicrohttpd is not available (yet) on CCI")

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def build_requirements(self):
        self.build_requires("automake/1.16.4")
        self.build_requires("m4/1.4.19")
        self.build_requires("flex/2.6.4")
        self.build_requires("bison/3.7.6")
        self.build_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                "--disable-werror",
                "--enable-static={}".format("no" if self.options.shared else "yes"),
                "--enable-deterministic-archives",
                "--enable-silent-rules",
                "--with-zlib",
                "--with-bzlib" if self.options.with_bzlib else "--without-bzlib",
                "--with-lzma" if self.options.with_lzma else "--without-lzma",
                "--enable-debuginfod" if self.options.debuginfod else "--disable-debuginfod",
            ]
            if Version(self.version) >= "0.186":
                args.append(
                    "--enable-libdebuginfod" if self.options.libdebuginfod else "--disable-libdebuginfod"
                )
            args.append("BUILD_STATIC={}".format("0" if self.options.shared else "1"))

            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.configure(configure_dir=self.source_folder, args=args)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            self.run("autoreconf -fiv")
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        copy(
            self,
            pattern="COPYING*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        autotools = self._configure_autotools()
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"), recursive=True)
        else:
            rm(self, "*.so", os.path.join(self.package_folder, "lib"), recursive=True)
            rm(self, "*.so.1", os.path.join(self.package_folder, "lib"), recursive=True)

    def package_info(self):
        # library components
        self.cpp_info.components["libelf"].libs = ["elf"]
        self.cpp_info.components["libelf"].requires = ["zlib::zlib"]

        self.cpp_info.components["libdw"].libs = ["dw"]
        self.cpp_info.components["libdw"].requires = ["libelf", "zlib::zlib"]
        if self.options.with_bzlib:
            self.cpp_info.components["libdw"].requires.append("bzip2::bzip2")
        if self.options.with_lzma:
            self.cpp_info.components["libdw"].requires.append("xz_utils::xz_utils")

        self.cpp_info.components["libasm"].includedirs = ["include/elfutils"]
        self.cpp_info.components["libasm"].libs = ["asm"]
        self.cpp_info.components["libasm"].requires = ["libelf", "libdw"]

        if self.options.get_safe("libdebuginfod"):
            self.cpp_info.components["libdebuginfod"].libs = ["debuginfod"]
            self.cpp_info.components["libdebuginfod"].requires = ["libcurl::curl"]

        # utilities
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var with : {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        bin_ext = ".exe" if self.settings.os == "Windows" else ""

        addr2line = unix_path(self, os.path.join(self.package_folder, "bin", "eu-addr2line" + bin_ext))
        self.output.info("Setting ADDR2LINE to {}".format(addr2line))
        self.env_info.ADDR2LINE = addr2line

        ar = unix_path(self, os.path.join(self.package_folder, "bin", "eu-ar" + bin_ext))
        self.output.info("Setting AR to {}".format(ar))
        self.env_info.AR = ar

        elfclassify = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfclassify" + bin_ext))
        self.output.info("Setting ELFCLASSIFY to {}".format(elfclassify))
        self.env_info.ELFCLASSIFY = elfclassify

        elfcmp = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfcmp" + bin_ext))
        self.output.info("Setting ELFCMP to {}".format(elfcmp))
        self.env_info.ELFCMP = elfcmp

        elfcompress = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfcompress" + bin_ext))
        self.output.info("Setting ELFCOMPRESS to {}".format(elfcompress))
        self.env_info.ELFCOMPRESS = elfcompress

        elflint = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elflint" + bin_ext))
        self.output.info("Setting ELFLINT to {}".format(elflint))
        self.env_info.ELFLINT = elflint

        findtextrel = unix_path(self, os.path.join(self.package_folder, "bin", "eu-findtextrel" + bin_ext))
        self.output.info("Setting FINDTEXTREL to {}".format(findtextrel))
        self.env_info.FINDTEXTREL = findtextrel

        make_debug_archive = unix_path(
            self, os.path.join(self.package_folder, "bin", "eu-make-debug-archive" + bin_ext)
        )
        self.output.info("Setting MAKE_DEBUG_ARCHIVE to {}".format(make_debug_archive))
        self.env_info.MAKE_DEBUG_ARCHIVE = make_debug_archive

        nm = unix_path(self, os.path.join(self.package_folder, "bin", "eu-nm" + bin_ext))
        self.output.info("Setting NM to {}".format(nm))
        self.env_info.NM = nm

        objdump = unix_path(self, os.path.join(self.package_folder, "bin", "eu-objdump" + bin_ext))
        self.output.info("Setting OBJDUMP to {}".format(objdump))
        self.env_info.OBJDUMP = objdump

        ranlib = unix_path(self, os.path.join(self.package_folder, "bin", "eu-ranlib" + bin_ext))
        self.output.info("Setting RANLIB to {}".format(ranlib))
        self.env_info.RANLIB = ranlib

        readelf = unix_path(self, os.path.join(self.package_folder, "bin", "eu-readelf" + bin_ext))
        self.output.info("Setting READELF to {}".format(readelf))
        self.env_info.READELF = readelf

        size = unix_path(self, os.path.join(self.package_folder, "bin", "eu-size" + bin_ext))
        self.output.info("Setting SIZE to {}".format(size))
        self.env_info.SIZE = size

        stack = unix_path(self, os.path.join(self.package_folder, "bin", "eu-stack" + bin_ext))
        self.output.info("Setting STACK to {}".format(stack))
        self.env_info.STACK = stack

        strings = unix_path(self, os.path.join(self.package_folder, "bin", "eu-strings" + bin_ext))
        self.output.info("Setting STRINGS to {}".format(strings))
        self.env_info.STRINGS = strings

        strip = unix_path(self, os.path.join(self.package_folder, "bin", "eu-strip" + bin_ext))
        self.output.info("Setting STRIP to {}".format(strip))
        self.env_info.STRIP = strip

        unstrip = unix_path(self, os.path.join(self.package_folder, "bin", "eu-unstrip" + bin_ext))
        self.output.info("Setting UNSTRIP to {}".format(unstrip))
        self.env_info.UNSTRIP = unstrip
