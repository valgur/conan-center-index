# TODO: verify the Conan v2 migration

import os
import shutil

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
from conan.tools.microsoft import msvc_runtime_flag, is_msvc_static_runtime, is_msvc

required_conan_version = ">=1.35.0"


class NvclothConan(ConanFile):
    name = "nvcloth"
    license = "Nvidia Source Code License (1-Way Commercial)"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/NVIDIAGameWorks/NvCloth"
    description = "NvCloth is a library that provides low level access to a cloth solver designed for realtime interactive applications."
    topics = ("physics", "physics-engine", "physics-simulation", "game-development", "cuda")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_cuda": [True, False],
        "use_dx11": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_cuda": False,
        "use_dx11": False,
    }

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        if self.settings.os not in ["Windows", "Linux", "Macos", "Android", "iOS"]:
            raise ConanInvalidConfiguration("Current os is not supported")

        build_type = self.settings.build_type
        if build_type not in ["Debug", "RelWithDebInfo", "Release"]:
            raise ConanInvalidConfiguration("Current build_type is not supported")

        if is_msvc(self) and Version(self.settings.compiler.version) < 9:
            raise ConanInvalidConfiguration("Visual Studio versions < 9 are not supported")

    def _remove_samples(self):
        rmdir(self, os.path.join(self.source_folder, "NvCloth", "samples"))

    def _patch_sources(self):
        # There is no reason to force consumer of PhysX public headers to use one of
        # NDEBUG or _DEBUG, since none of them relies on NDEBUG or _DEBUG
        replace_in_file(
            self,
            os.path.join(
                self.build_folder, self.source_folder, "PxShared", "include", "foundation", "PxPreprocessor.h"
            ),
            "#error Exactly one of NDEBUG and _DEBUG needs to be defined!",
            "// #error Exactly one of NDEBUG and _DEBUG needs to be defined!",
        )
        shutil.copy(
            os.path.join(self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"),
            os.path.join(self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.origin"),
        )
        apply_conandata_patches(self)

        if self.settings.build_type == "Debug":
            shutil.copy(
                os.path.join(self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"),
                os.path.join(
                    self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.patched"
                ),
            )
            shutil.copy(
                os.path.join(
                    self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.origin"
                ),
                os.path.join(self.build_folder, self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"),
            )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def generate(self):
        tc = CMakeToolchain(self)
        if not self.options.shared:
            tc.variables["PX_STATIC_LIBRARIES"] = 1
        tc.variables["STATIC_WINCRT"] = is_msvc_static_runtime(self)
        tc.variables["NV_CLOTH_ENABLE_CUDA"] = self.options.use_cuda
        tc.variables["NV_CLOTH_ENABLE_DX11"] = self.options.use_dx11
        tc.variables["TARGET_BUILD_PLATFORM"] = self._get_target_build_platform()
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        with environment_append(self, {"GW_DEPS_ROOT": os.path.abspath(self.source_folder)}):
            self._patch_sources()
            self._remove_samples()
            cmake = CMake(self)
            cmake.configure(build_script_folder=f"NvCloth/compiler/cmake/{self._get_target_build_platform()}")
            cmake.build()

    def _get_build_type(self):
        if self.settings.build_type == "Debug":
            return "debug"
        elif self.settings.build_type == "RelWithDebInfo":
            return "checked"
        elif self.settings.build_type == "Release":
            return "release"

    def _get_target_build_platform(self):
        return {
            "Windows": "windows",
            "Linux": "linux",
            "Macos": "mac",
            "Android": "android",
            "iOS": "ios",
        }.get(str(self.settings.os))

    def package(self):
        if self.settings.build_type == "Debug":
            shutil.copy(
                os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.patched"),
                os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"),
            )
        nvcloth_source_subfolder = os.path.join(self.build_folder, self.source_folder)
        nvclothbuild_folder = os.path.join(self.build_folder, self.build_folder)

        copy(
            self,
            pattern="NvCloth/license.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=nvcloth_source_subfolder,
            keep_path=False,
        )
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(nvcloth_source_subfolder, "NvCloth", "include"),
        )
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(nvcloth_source_subfolder, "NvCloth", "extensions", "include"),
        )
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(nvcloth_source_subfolder, "PxShared", "include"),
        )
        copy(
            self,
            "*.a",
            dst=os.path.join(self.package_folder, "lib"),
            src=nvclothbuild_folder,
            keep_path=False,
        )
        copy(
            self,
            "*.lib",
            dst=os.path.join(self.package_folder, "lib"),
            src=nvclothbuild_folder,
            keep_path=False,
        )
        copy(
            self,
            "*.dylib*",
            dst=os.path.join(self.package_folder, "lib"),
            src=nvclothbuild_folder,
            keep_path=False,
        )
        copy(
            self,
            "*.dll",
            dst=os.path.join(self.package_folder, "bin"),
            src=nvclothbuild_folder,
            keep_path=False,
        )
        copy(
            self,
            "*.so",
            dst=os.path.join(self.package_folder, "lib"),
            src=nvclothbuild_folder,
            keep_path=False,
        )

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "nvcloth"
        self.cpp_info.names["cmake_find_package_multi"] = "nvcloth"

        if self.settings.build_type == "Debug":
            debug_suffix = "DEBUG"
        else:
            debug_suffix = ""

        if self.settings.os == "Windows":
            if self.settings.arch == "x86_64":
                arch_suffix = "x64"
            else:
                arch_suffix = ""
            self.cpp_info.libs = ["NvCloth{}_{}".format(debug_suffix, arch_suffix)]
        else:
            self.cpp_info.libs = ["NvCloth{}".format(debug_suffix)]

        if not self.options.shared:
            if self.settings.os in ("FreeBSD", "Linux"):
                self.cpp_info.system_libs.append("m")
