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

required_conan_version = ">=1.33.0"


class SrtConan(ConanFile):
    name = "srt"
    homepage = "https://github.com/Haivision/srt"
    description = "Secure Reliable Transport (SRT) is an open source transport technology that optimizes streaming performance across unpredictable networks, such as the Internet."
    topics = ("ip", "transport")
    url = "https://github.com/conan-io/conan-center-index"
    license = "MPL-2.0"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _has_stdcxx_sync(self):
        return Version(self.version) >= "1.4.2"

    @property
    def _has_posix_threads(self):
        return not (
            self.settings.os == "Windows"
            and (
                self.settings.compiler == "Visual Studio"
                or (self.settings.compiler == "gcc" and self.settings.compiler.get_safe("threads") == "win32")
            )
        )

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("openssl/1.1.1q")
        if not self._has_posix_threads and not self._has_stdcxx_sync:
            self.requires("pthreads4w/3.0.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            'set (CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/scripts")',
            'list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/scripts")',
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_APPS"] = False
        tc.variables["ENABLE_LOGGING"] = False
        tc.variables["ENABLE_SHARED"] = self.options.shared
        tc.variables["ENABLE_STATIC"] = not self.options.shared
        if self._has_stdcxx_sync:
            tc.variables["ENABLE_STDCXX_SYNC"] = True
        tc.variables["ENABLE_ENCRYPTION"] = True
        tc.variables["USE_OPENSSL_PC"] = False
        if self.settings.compiler == "Visual Studio":
            # required to avoid warnings when srt shared, even if openssl shared,
            # otherwise upstream CMakeLists would add /DELAYLOAD:libeay32.dll to link flags
            tc.variables["OPENSSL_USE_STATIC_LIBS"] = True
        if not self._has_posix_threads and not self._has_stdcxx_sync:
            # TODO
            # set(PTHREAD_LIBRARY "${CONAN_LIBS_PTHREADS4W}")
            # set(PTHREAD_INCLUDE_DIR "${CONAN_INCLUDE_DIRS_PTHREADS4W}")
            pass
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "srt"
        suffix = "_static" if self.settings.compiler == "Visual Studio" and not self.options.shared else ""
        self.cpp_info.libs = ["srt" + suffix]
        if self.options.shared:
            self.cpp_info.defines = ["SRT_DYNAMIC"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]
