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
import glob
import os
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class CoseCConan(ConanFile):
    name = "cose-c"
    license = "BSD-3-Clause"
    homepage = "https://github.com/cose-wg/COSE-C"
    url = "https://github.com/conan-io/conan-center-index"
    description = """Implementation of COSE in C using cn-cbor and openssl"""
    topics = "cbor"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False], "with_ssl": ["openssl", "mbedtls"]}
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": "openssl",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("cn-cbor/1.0.0")

        if self.options.with_ssl == "mbedtls":
            self.requires("mbedtls/2.23.0")
        else:
            self.requires("openssl/1.1.1h")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(glob.glob("COSE-C-*")[0], self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["COSE_C_COVERALLS"] = False
        tc.variables["COSE_C_BUILD_TESTS"] = False
        tc.variables["COSE_C_BUILD_DOCS"] = False
        tc.variables["COSE_C_BUILD_DUMPER"] = False
        tc.variables["COSE_C_USE_MBEDTLS"] = self.options.with_ssl == "mbedtls"
        tc.variables["COSE_C_USE_FIND_PACKAGE"] = True
        tc.variables["COSE_C_EXPORT_TARGETS"] = True
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "secur32", "crypt32", "bcrypt"])
        if self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["CoreFoundation", "Security"])
        if self.options.with_ssl == "mbedtls":
            self.cpp_info.defines.append("COSE_C_USE_MBEDTLS")
        else:
            self.cpp_info.defines.append("COSE_C_USE_OPENSSL")
