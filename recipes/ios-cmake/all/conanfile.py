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


class IosCMakeConan(ConanFile):
    name = "ios-cmake"
    license = "BSD-3-Clause"
    settings = "os", "arch"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/leetal/ios-cmake"
    options = {
        "enable_bitcode": [True, False],
        "enable_arc": [True, False],
        "enable_visibility": [True, False],
        "enable_strict_try_compile": [True, False],
        "toolchain_target": [
            "auto",
            "OS",
            "OS64",
            "OS64COMBINED",
            "SIMULATOR",
            "SIMULATOR64",
            "SIMULATORARM64",
            "TVOS",
            "TVOSCOMBINED",
            "SIMULATOR_TVOS",
            "WATCHOS",
            "WATCHOSCOMBINED",
            "SIMULATOR_WATCHOS",
            "MAC",
            "MAC_ARM64",
            "MAC_CATALYST",
            "MAC_CATALYST_ARM64",
        ],
    }
    default_options = {
        "enable_bitcode": True,
        "enable_arc": True,
        "enable_visibility": False,
        "enable_strict_try_compile": False,
        "toolchain_target": "auto",
    }
    description = "ios Cmake toolchain to (cross) compile macOS/iOS/watchOS/tvOS"
    topics = ("apple", "ios", "cmake", "toolchain", "ios", "tvos", "watchos")

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def export_sources(self):
        copy(self, "cmake-wrapper", src=self.recipe_folder, dst=self.export_sources_folder)

    def configure(self):
        if not is_apple_os(self.settings.os):
            raise ConanInvalidConfiguration("This package only supports Apple operating systems")

    def _guess_toolchain_target(self, os, arch):
        if os == "iOS":
            if arch in ["armv8", "armv8.3"]:
                return "OS64"
            if arch == "x86_64":
                return "SIMULATOR64"
            # 32bit is dead, don't care
        elif os == "watchOS":
            if arch == "x86_64":
                return "SIMULATOR_WATCHOS"
            else:
                return "WATCHOS"
        elif os == "tvOS":
            if arch == "x86_64":
                return "TVOS"
            else:
                return "SIMULATOR_TVOS"
        raise ConanInvalidConfiguration(
            "Can not guess toolchain_target. Please set the option explicit (or check our os settings)"
        )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(f"ios-cmake-{self.version}", self.source_folder)

    def build(self):
        pass  # there is nothing to build

    def package(self):
        copy(self, "cmake-wrapper", dst=os.path.join(self.package_folder, "bin"))
        copy(
            self,
            "ios.toolchain.cmake",
            src=self.source_folder,
            dst=os.path.join("lib", "cmake", "ios-cmake"),
            keep_path=False,
        )
        self._chmod_plus_x(os.path.join(self.package_folder, "bin", "cmake-wrapper"))

        copy(
            self,
            "LICENSE.md",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
            keep_path=False,
        )
        # satisfy KB-H014 (header_only recipes require headers)
        save(self, os.path.join(self.package_folder, "include", "dummy_header.h"), "\n")

    def package_info(self):
        if self.settings.os == "Macos":
            if not getattr(self, "settings_target", None):
                #  not a build_require , but can be fine since its build as a ppr:b, but nothing to do
                return
            # this is where I want to be, expecting this as a build_require for a host
            target_os = str(self.settings_target.os)
            arch_flag = self.settings_target.arch
            target_version = self.settings_target.os.version
        elif self.settings.os == "iOS":  # old style 1 profile, don't use
            target_os = str(self.settings.os)
            arch_flag = self.settings.arch
            target_version = self.settings.os.version
        else:
            # hackingtosh ? hu
            raise ConanInvalidConfiguration("Building for iOS on a non Mac platform? Please tell me how!")

        if self.options.toolchain_target == "auto":
            toolchain_target = self._guess_toolchain_target(target_os, arch_flag)
        else:
            toolchain_target = self.options.toolchain_target

        if arch_flag == "armv8":
            arch_flag = "arm64"
        elif arch_flag == "armv8.3":
            arch_flag = "arm64e"

        cmake_options = "-DENABLE_BITCODE={} -DENABLE_ARC={} -DENABLE_VISIBILITY={} -DENABLE_STRICT_TRY_COMPILE={}".format(
            self.options.enable_bitcode,
            self.options.enable_arc,
            self.options.enable_visibility,
            self.options.enable_strict_try_compile,
        )
        # Note that this, as long as we specify (overwrite) the ARCHS, PLATFORM has just limited effect,
        # but PLATFORM need to be set in the profile so it makes sense, see ios-cmake docs for more info
        cmake_flags = "-DPLATFORM={} -DDEPLOYMENT_TARGET={} -DARCHS={} {}".format(
            toolchain_target, target_version, arch_flag, cmake_options
        )

        self.env_info.CONAN_USER_CMAKE_FLAGS = cmake_flags
        self.output.info("Setting toolchain options to: {}".format(cmake_flags))
        cmake_wrapper = os.path.join(self.package_folder, "bin", "cmake-wrapper")
        self.output.info("Setting CONAN_CMAKE_PROGRAM to: {}".format(cmake_wrapper))
        self.env_info.CONAN_CMAKE_PROGRAM = cmake_wrapper
        tool_chain = os.path.join(self.package_folder, "lib", "cmake", "ios-cmake", "ios.toolchain.cmake")
        self.env_info.CONAN_CMAKE_TOOLCHAIN_FILE = tool_chain
        # add some more env_info, for the case users generate a toolchain file via conan and want to access that info
        self.env_info.CONAN_ENABLE_BITCODE_FLAG = str(self.options.enable_bitcode)
        self.env_info.CONAN_ENABLE_ARC_FLAG = str(self.options.enable_arc)
        self.env_info.CONAN_ENABLE_VISIBILITY_FLAG = str(self.options.enable_visibility)
        self.env_info.CONAN_ENABLE_STRICT_TRY_COMPILE_FLAG = str(self.options.enable_strict_try_compile)
        # the rest should be exported from profile info anyway

    def package_id(self):
        self.info.header_only()
        # TODO , since we have 2 profiles I am not sure that this is still required
        # since this will always be / has to be  a build profile
