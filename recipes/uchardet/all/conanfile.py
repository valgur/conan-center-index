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
import functools

required_conan_version = ">=1.33.0"


class UchardetConan(ConanFile):
    name = "uchardet"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/freedesktop/uchardet"
    description = "uchardet is an encoding detector library, which takes a sequence of bytes in an unknown character encoding and attempts to determine the encoding of the text. Returned encoding names are iconv-compatible."
    topics = ("encoding", "detector")
    license = "MPL-1.1"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "check_sse2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "check_sse2": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self._settings_build not in ("x86", "x86_64"):
            self.options.rm_safe("check_sse2")
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        # the following fixes that apply to uchardet version 0.0.7
        # fix broken cmake
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "${CMAKE_BINARY_DIR}",
            "${CMAKE_CURRENT_BINARY_DIR}",
        )
        # fix problem with mac os
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "string(TOLOWER ${CMAKE_SYSTEM_PROCESSOR} TARGET_ARCHITECTURE)",
            'string(TOLOWER "${CMAKE_SYSTEM_PROCESSOR}" TARGET_ARCHITECTURE)',
        )
        # disable building tests
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "add_subdirectory(test)",
            "#add_subdirectory(test)",
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CHECK_SSE2"] = self.options.get_safe("check_sse2", False)
        tc.variables["BUILD_BINARY"] = False
        tc.variables[
            "BUILD_STATIC"
        ] = False  # disable building static libraries when self.options.shared is True
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "uchardet")
        self.cpp_info.set_property("cmake_target_name", "uchardet")
        self.cpp_info.set_property("pkg_config_name", "libuchardet")

        self.cpp_info.names["cmake_find_package"] = "uchardet"
        self.cpp_info.names["cmake_find_package_multi"] = "uchardet"
        self.cpp_info.names["pkgconfig"] = "libuchardet"
        self.cpp_info.libs = ["uchardet"]
        if self.options.shared:
            self.cpp_info.defines.append("UCHARDET_SHARED")
