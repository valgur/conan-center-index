# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path
from conan.tools.scm import Version

required_conan_version = ">=1.47.0"


class ElfutilsConan(ConanFile):
    name = "elfutils"
    description = (
        "A dwarf, dwfl and dwelf functions to read DWARF, "
        "find separate debuginfo, symbols and inspect process state."
    )
    license = ["GPL-1.0-or-later", "LGPL-3.0-or-later", "GPL-2.0-or-later"]
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sourceware.org/elfutils"
    topics = ("libelf", "libdw", "libasm")

    package_type = "library"
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

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

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

    def layout(self):
        basic_layout(self, src_folder="src")

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

    def validate(self):
        if Version(self.version) >= "0.186":
            if self.settings.compiler in ["Visual Studio", "apple-clang", "msvc"]:
                raise ConanInvalidConfiguration(
                    f"Compiler {self.settings.compiler} not supported. elfutils only supports gcc and clang"
                )
        else:
            if self.settings.compiler in ["Visual Studio", "clang", "apple-clang", "msvc"]:
                raise ConanInvalidConfiguration(
                    f"Compiler {self.settings.compiler} not supported. elfutils only supports gcc"
                )
        if self.settings.compiler != "gcc":
            self.output.warning(f"Compiler {self.settings.compiler} is not gcc.")

    def build_requirements(self):
        self.tool_requires("automake/1.16.5")
        self.tool_requires("m4/1.4.19")
        self.tool_requires("flex/2.6.4")
        self.tool_requires("bison/3.7.6")
        self.tool_requires("pkgconf/1.9.3")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args += [
            "--disable-werror",
            "--enable-deterministic-archives",
            "--enable-silent-rules",
            "--with-zlib",
            "--with-bzlib" if self.options.with_bzlib else "--without-bzlib",
            "--with-lzma" if self.options.with_lzma else "--without-lzma",
            "--enable-debuginfod" if self.options.debuginfod else "--disable-debuginfod",
        ]
        if Version(self.version) >= "0.186":
            args.append("--enable-libdebuginfod" if self.options.libdebuginfod else "--disable-libdebuginfod")
        args.append("BUILD_STATIC={}".format("0" if self.options.shared else "1"))
        tc.configure(configure_dir=self.source_folder, args=args)
        tc.generate()

        tc = PkgConfigDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.make()

    def package(self):
        copy(
            self,
            pattern="COPYING*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        autotools = Autotools(self)
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
        self.output.info(f"Appending PATH env var with : {bin_path}")
        self.env_info.PATH.append(bin_path)

        bin_ext = ".exe" if self.settings.os == "Windows" else ""

        addr2line = unix_path(self, os.path.join(self.package_folder, "bin", "eu-addr2line" + bin_ext))
        self.output.info(f"Setting ADDR2LINE to {addr2line}")
        self.env_info.ADDR2LINE = addr2line

        ar = unix_path(self, os.path.join(self.package_folder, "bin", "eu-ar" + bin_ext))
        self.output.info(f"Setting AR to {ar}")
        self.env_info.AR = ar

        elfclassify = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfclassify" + bin_ext))
        self.output.info(f"Setting ELFCLASSIFY to {elfclassify}")
        self.env_info.ELFCLASSIFY = elfclassify

        elfcmp = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfcmp" + bin_ext))
        self.output.info(f"Setting ELFCMP to {elfcmp}")
        self.env_info.ELFCMP = elfcmp

        elfcompress = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elfcompress" + bin_ext))
        self.output.info(f"Setting ELFCOMPRESS to {elfcompress}")
        self.env_info.ELFCOMPRESS = elfcompress

        elflint = unix_path(self, os.path.join(self.package_folder, "bin", "eu-elflint" + bin_ext))
        self.output.info(f"Setting ELFLINT to {elflint}")
        self.env_info.ELFLINT = elflint

        findtextrel = unix_path(self, os.path.join(self.package_folder, "bin", "eu-findtextrel" + bin_ext))
        self.output.info(f"Setting FINDTEXTREL to {findtextrel}")
        self.env_info.FINDTEXTREL = findtextrel

        make_debug_archive = unix_path(
            self, os.path.join(self.package_folder, "bin", "eu-make-debug-archive" + bin_ext)
        )
        self.output.info(f"Setting MAKE_DEBUG_ARCHIVE to {make_debug_archive}")
        self.env_info.MAKE_DEBUG_ARCHIVE = make_debug_archive

        nm = unix_path(self, os.path.join(self.package_folder, "bin", "eu-nm" + bin_ext))
        self.output.info(f"Setting NM to {nm}")
        self.env_info.NM = nm

        objdump = unix_path(self, os.path.join(self.package_folder, "bin", "eu-objdump" + bin_ext))
        self.output.info(f"Setting OBJDUMP to {objdump}")
        self.env_info.OBJDUMP = objdump

        ranlib = unix_path(self, os.path.join(self.package_folder, "bin", "eu-ranlib" + bin_ext))
        self.output.info(f"Setting RANLIB to {ranlib}")
        self.env_info.RANLIB = ranlib

        readelf = unix_path(self, os.path.join(self.package_folder, "bin", "eu-readelf" + bin_ext))
        self.output.info(f"Setting READELF to {readelf}")
        self.env_info.READELF = readelf

        size = unix_path(self, os.path.join(self.package_folder, "bin", "eu-size" + bin_ext))
        self.output.info(f"Setting SIZE to {size}")
        self.env_info.SIZE = size

        stack = unix_path(self, os.path.join(self.package_folder, "bin", "eu-stack" + bin_ext))
        self.output.info(f"Setting STACK to {stack}")
        self.env_info.STACK = stack

        strings = unix_path(self, os.path.join(self.package_folder, "bin", "eu-strings" + bin_ext))
        self.output.info(f"Setting STRINGS to {strings}")
        self.env_info.STRINGS = strings

        strip = unix_path(self, os.path.join(self.package_folder, "bin", "eu-strip" + bin_ext))
        self.output.info(f"Setting STRIP to {strip}")
        self.env_info.STRIP = strip

        unstrip = unix_path(self, os.path.join(self.package_folder, "bin", "eu-unstrip" + bin_ext))
        self.output.info(f"Setting UNSTRIP to {unstrip}")
        self.env_info.UNSTRIP = unstrip
