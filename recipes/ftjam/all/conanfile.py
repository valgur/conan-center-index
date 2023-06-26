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


class FtjamConan(ConanFile):
    name = "ftjam"
    description = "Jam (ftjam) is a small open-source build tool that can be used as a replacement for Make."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.freetype.org/jam/"
    topics = ("build", "make", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("ftjam doesn't build with Visual Studio yet")
        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration("ftjam can't be cross-built")

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")
        if self.settings.compiler == "Visual Studio":
            self.build_requires("automake/1.16.2")
        if self.settings.os != "Windows":
            self.build_requires("bison/3.7.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "jamgram.c"), "\n#line", "\n//#line")

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            if self.settings.os == "Windows":
                # toolset name of the system building ftjam
                jam_toolset = self._jam_toolset(self.settings.os, self.settings.compiler)
                autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                autotools.libs = []
                env = autotools.vars
                with environment_append(self, env):
                    if self.settings.compiler == "Visual Studio":
                        with vcvars(self.settings):
                            self.run("nmake -f builds/win32-visualc.mk JAM_TOOLSET={}".format(jam_toolset))
                    else:
                        with environment_append(self, {"PATH": [os.getcwd()]}):
                            autotools.make(
                                args=["JAM_TOOLSET={}".format(jam_toolset), "-f", "builds/win32-gcc.mk"]
                            )
            else:
                with chdir(self, os.path.join(self.build_folder, "builds", "unix")):
                    autotools = Autotools(self)
                    autotools.configure()
                    autotools.make()

    def package(self):
        txt = load(self, os.path.join(self.source_folder, "jam.c"))
        license_txt = txt[: txt.find("*/") + 3]
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), license_txt)
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                pass
            else:
                copy(
                    self,
                    "*.exe",
                    src=os.path.join(self.source_folder, "bin.nt"),
                    dst=os.path.join(self.package_folder, "bin"),
                )
        else:
            with chdir(self, self.source_folder):
                autotools = self._configure_autotools()
                autotools.install()

    def _jam_toolset(self, os, compiler):
        if compiler == "Visual Studio":
            return "VISUALC"
        if compiler == "intel":
            return "INTELC"
        if os == "Windows":
            return "MINGW"
        return None

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        jam_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(jam_path))
        self.env_info.PATH.append(jam_path)

        jam_bin = os.path.join(jam_path, "jam")
        if self.settings.os == "Windows":
            jam_bin += ".exe"
        self.output.info("Setting JAM environment variable: {}".format(jam_bin))
        self.env_info.JAM = jam_bin

        # toolset of the system using ftjam
        jam_toolset = self._jam_toolset(self.settings.os, self.settings.compiler)
        if jam_toolset:
            self.output.info("Setting JAM_TOOLSET environment variable: {}".format(jam_toolset))
            self.env_info.JAM_TOOLSET = jam_toolset
