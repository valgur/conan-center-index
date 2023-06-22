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
from conan import ConanFile
from conan.tools.files import get, rmdir
import os
import functools


class SDLMixerConan(ConanFile):
    name = "sdl_mixer"
    description = "SDL_mixer is a sample multi-channel audio mixer library"
    topics = ("sdl2", "sdl", "mixer", "audio", "multimedia", "sound", "music")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.libsdl.org/projects/SDL_mixer/"
    license = "Zlib"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cmd": [True, False],
        "wav": [True, False],
        "flac": [True, False],
        "mpg123": [True, False],
        "mad": [True, False],
        "ogg": [True, False],
        "opus": [True, False],
        "mikmod": [True, False],
        "modplug": [True, False],
        "fluidsynth": [True, False],
        "nativemidi": [True, False],
        "tinymidi": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cmd": False,  # needs sys/wait.h
        "wav": True,
        "flac": True,
        "mpg123": True,
        "mad": True,
        "ogg": True,
        "opus": True,
        "mikmod": True,
        "modplug": True,
        "fluidsynth": False,  # TODO: add fluidsynth to Conan Center
        "nativemidi": True,
        "tinymidi": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            self.options.rm_safe("tinymidi")
        else:
            self.options.rm_safe("nativemidi")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("sdl/2.0.20")
        if self.options.flac:
            self.requires("flac/1.3.3")
        if self.options.mpg123:
            self.requires("mpg123/1.29.3")
        if self.options.mad:
            self.requires("libmad/0.15.1b")
        if self.options.ogg:
            self.requires("ogg/1.3.5")
            self.requires("vorbis/1.3.7")
        if self.options.opus:
            self.requires("openssl/1.1.1q")
            self.requires("opus/1.3.1")
            self.requires("opusfile/0.12")
        if self.options.mikmod:
            self.requires("libmikmod/3.3.11.1")
        if self.options.modplug:
            self.requires("libmodplug/0.8.9.0")
        if self.options.fluidsynth:
            self.requires("fluidsynth/2.2")  # TODO: this package is missing on the conan-center-index
        if self.settings.os == "Linux":
            if self.options.tinymidi:
                self.requires("tinymidi/cci.20130325")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

        rmdir(self, os.path.join(self.source_folder, "external"))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMD"] = self.options.cmd
        tc.variables["WAV"] = self.options.wav
        tc.variables["FLAC"] = self.options.flac
        tc.variables["MP3_MPG123"] = self.options.mpg123
        tc.variables["MP3_MAD"] = self.options.mad
        tc.variables["OGG"] = self.options.ogg
        tc.variables["OPUS"] = self.options.opus
        tc.variables["MOD_MIKMOD"] = self.options.mikmod
        tc.variables["MOD_MODPLUG"] = self.options.modplug
        tc.variables["MID_FLUIDSYNTH"] = self.options.fluidsynth
        if self.settings.os == "Linux":
            tc.variables["MID_TINYMIDI"] = self.options.tinymidi
            tc.variables["MID_NATIVE"] = False
        else:
            tc.variables["MID_TINYMIDI"] = False
            tc.variables["MID_NATIVE"] = self.options.nativemidi

        tc.variables["FLAC_DYNAMIC"] = self.options["flac"].shared if self.options.flac else False
        tc.variables["MP3_MPG123_DYNAMIC"] = self.options["mpg123"].shared if self.options.mpg123 else False
        tc.variables["OGG_DYNAMIC"] = self.options["ogg"].shared if self.options.ogg else False
        tc.variables["OPUS_DYNAMIC"] = self.options["opus"].shared if self.options.opus else False
        tc.variables["MOD_MIKMOD_DYNAMIC"] = (
            self.options["libmikmod"].shared if self.options.mikmod else False
        )
        tc.variables["MOD_MODPLUG_DYNAMIC"] = (
            self.options["libmodplug"].shared if self.options.modplug else False
        )
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="COPYING.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "SDL2_mixer")
        self.cpp_info.set_property("cmake_file_name", "SDL2_mixer")
        self.cpp_info.set_property("cmake_target_name", "SDL2_mixer::SDL2_mixer")
        self.cpp_info.set_property("pkg_config_name", "SDL2_mixer")
        self.cpp_info.libs = ["SDL2_mixer"]
        self.cpp_info.includedirs.append(os.path.join("include", "SDL2"))

        self.cpp_info.names["cmake_find_package"] = "SDL2_mixer"
        self.cpp_info.names["cmake_find_package_multi"] = "SDL2_mixer"
