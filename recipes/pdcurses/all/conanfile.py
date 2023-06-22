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
import re


class PDCursesConan(ConanFile):
    name = "pdcurses"
    description = "PDCurses - a curses library for environments that don't fit the termcap/terminfo model"
    topics = ("curses", "ncurses")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://pdcurses.org/"
    license = "Unlicense", "MITX", "CC-BY-4.0", "GPL", "FSFUL"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_widec": [True, False],
        "with_sdl": [None, "1", "2"],
    }
    default_options = {"shared": False, "fPIC": True, "enable_widec": False, "with_sdl": None}

    _autotools = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ("FreeBSD", "Linux"):
            del self.options.enable_widec

    def configure(self):
        if tools.is_apple_os(self.settings.os):
            raise ConanInvalidConfiguration("pdcurses does not support Apple")
        if self.options.with_sdl:
            raise ConanInvalidConfiguration("conan-center-index has no packages for sdl (yet)")
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def requirements(self):
        if self.settings.os in ("FreeBSD", "Linux"):
            self.requires("xorg/system")

    def build_requirements(self):
        if self.settings.compiler != "Visual Studio":
            self.build_requires("make/4.2.1")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("PDCurses-{}".format(self.version), self._source_subfolder)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        conf_args = [
            "--enable-shared" if self.options.shared else "--disable-shared",
            "--enable-widec" if self.options.enable_widec else "--disable-widec",
        ]
        self._autotools.configure(args=conf_args)
        return self._autotools

    def _build_windows(self):
        with tools.chdir(os.path.join(self._source_subfolder, "wincon")):
            args = []
            if self.options.shared:
                args.append("DLL=Y")
            args = " ".join(args)
            if self.settings.compiler == "Visual Studio":
                with tools.vcvars(self):
                    self.run("nmake -f Makefile.vc {}".format(args))
            else:
                self.run("{} libs {}".format(os.environ["CONAN_MAKE_PROGRAM"], args))

    def _patch_sources(self):
        if self.settings.compiler == "Visual Studio":
            tools.replace_in_file(
                os.path.join(self._source_subfolder, "wincon", "Makefile.vc"),
                "$(CFLAGS)",
                "$(CFLAGS) -{}".format(self.settings.compiler.runtime),
            )
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "x11", "Makefile.in"),
            "$(INSTALL) -c -m 644 $(osdir)/libXCurses.a $(libdir)/libXCurses.a",
            "-$(INSTALL) -c -m 644 $(osdir)/libXCurses.a $(libdir)/libXCurses.a",
        )
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "x11", "Makefile.in"),
            "\nall:\t",
            "\nall:\t{}\t#".format("@SHL_TARGETS@" if self.options.shared else "$(LIBCURSES)"),
        )

    def build(self):
        self._patch_sources()
        if self.settings.os == "Windows":
            self._build_windows()
        else:
            with tools.chdir(os.path.join(self._source_subfolder, "x11")):
                autotools = self._configure_autotools()
                autotools.make()

    @property
    def _subsystem_folder(self):
        return {
            "Windows": "wincon",
        }.get(str(self.settings.os), "x11")

    @property
    def _license_text(self):
        readme = tools.load(os.path.join(self._source_subfolder, self._subsystem_folder, "README.md"))
        match = re.search(
            r"Distribution Status\n[\-]+(?:[\r\n])+((?:[0-9a-z .,;*]+[\r\n])+)",
            readme,
            re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            raise ConanException("Cannot extract distribution status")
        return match.group(1).strip() + "\n"

    def package(self):
        tools.save(os.path.join(self.package_folder, "licenses", "LICENSE"), self._license_text)

        if self.settings.os == "Windows":
            self.copy(pattern="curses.h", src=self._source_subfolder, dst="include")
            self.copy(pattern="*.dll", dst="bin", keep_path=False)
            self.copy(pattern="*.lib", dst="lib", keep_path=False)
            self.copy(pattern="*.a", dst="lib", keep_path=False)

            if self.settings.compiler != "Visual Studio":
                os.rename(
                    os.path.join(self.package_folder, "lib", "pdcurses.a"),
                    os.path.join(self.package_folder, "lib", "libpdcurses.a"),
                )
        else:
            with tools.chdir(os.path.join(self._source_subfolder, "x11")):
                autotools = self._configure_autotools()
                autotools.install()
                tools.rmdir(os.path.join(self.package_folder, "bin"))

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["pdcurses"]
        elif self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.includedirs.append(os.path.join("include", "xcurses"))
            self.cpp_info.libs = ["XCurses"]
