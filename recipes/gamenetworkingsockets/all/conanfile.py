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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class GameNetworkingSocketsConan(ConanFile):
    name = "gamenetworkingsockets"
    description = "GameNetworkingSockets is a basic transport layer for games."
    topics = ("networking", "game-development")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ValveSoftware/GameNetworkingSockets"
    license = "BSD-3-Clause"
    generators = "cmake", "pkg_config"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "encryption": ["openssl", "libsodium", "bcrypt"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "encryption": "openssl",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

        if self.options.encryption == "bcrypt" and self.settings.os != "Windows":
            raise ConanInvalidConfiguration("bcrypt is only valid on Windows")

    def build_requirements(self):
        self.build_requires("protobuf/3.17.1")

    def requirements(self):
        self.requires("protobuf/3.17.1")
        if self.options.encryption == "openssl":
            self.requires("openssl/1.1.1l")
        elif self.options.encryption == "libsodium":
            self.requires("libsodium/1.0.18")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["GAMENETWORKINGSOCKETS_BUILD_EXAMPLES"] = False
        tc.variables["GAMENETWORKINGSOCKETS_BUILD_TESTS"] = False
        tc.variables["Protobuf_USE_STATIC_LIBS"] = not self.options["protobuf"].shared
        crypto = {
            "openssl": "OpenSSL",
            "libsodium": "libsodium",
            "bcrypt": "BCrypt",
        }
        tc.variables["USE_CRYPTO"] = crypto[str(self.options.encryption)]
        crypto25519 = {
            "openssl": "OpenSSL",
            "libsodium": "libsodium",
            "bcrypt": "Reference",
        }
        tc.variables["USE_CRYPTO25519"] = crypto25519[str(self.options.encryption)]
        if self.options.encryption == "openssl":
            tc.variables["OPENSSL_NEW_ENOUGH"] = True
            tc.variables["OPENSSL_HAS_25519_RAW"] = True
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "GameNetworkingSockets"
        self.cpp_info.names["cmake_find_package_multi"] = "GameNetworkingSockets"
        self.cpp_info.names["pkg_config"] = "GameNetworkingSockets"
        self.cpp_info.includedirs.append(os.path.join("include", "GameNetworkingSockets"))
        if self.options.shared:
            self.cpp_info.libs = ["GameNetworkingSockets"]
        else:
            self.cpp_info.libs = ["GameNetworkingSockets_s"]
            self.cpp_info.defines = ["STEAMNETWORKINGSOCKETS_STATIC_LINK"]

        self.cpp_info.requires = ["protobuf::libprotobuf"]
        if self.options.encryption == "openssl":
            self.cpp_info.requires += ["openssl::crypto"]
        elif self.options.encryption == "libsodium":
            self.cpp_info.requires += ["libsodium::libsodium"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "crypt32", "winmm"]
            if self.options.encryption == "bcrypt":
                self.cpp_info.system_libs += ["bcrypt"]
