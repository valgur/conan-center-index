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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class CassandraCppDriverConan(ConanFile):
    name = "cassandra-cpp-driver"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://docs.datastax.com/en/developer/cpp-driver/"
    description = "DataStax C/C++ Driver for Apache Cassandra and DataStax Products"
    topics = ("cassandra", "cpp-driver", "database", "conan-recipe")

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "install_header_in_subdir": [True, False],
        "use_atomic": [None, "boost", "std"],
        "with_openssl": [True, False],
        "with_zlib": [True, False],
        "with_kerberos": [True, False],
        "use_timerfd": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "install_header_in_subdir": False,
        "use_atomic": None,
        "with_openssl": True,
        "with_zlib": True,
        "with_kerberos": False,
        "use_timerfd": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            self.options.rm_safe("use_timerfd")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("libuv/1.44.1")
        self.requires("http_parser/2.9.4")
        self.requires("rapidjson/cci.20211112")

        if self.options.with_openssl:
            self.requires("openssl/1.1.1q")

        if self.options.with_zlib:
            self.requires("minizip/1.2.12")
            self.requires("zlib/1.2.12")

        if self.options.use_atomic == "boost":
            self.requires("boost/1.79.0")

    def validate(self):
        if self.options.use_atomic == "boost":
            # Compilation error on Linux
            if self.settings.os == "Linux":
                raise ConanInvalidConfiguration("Boost.Atomic is not supported on Linux at the moment")

        if self.options.with_kerberos:
            raise ConanInvalidConfiguration("Kerberos is not supported at the moment")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            '"${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang"',
            '"${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang"',
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["VERSION"] = self.version
        tc.variables["CASS_BUILD_EXAMPLES"] = False
        tc.variables["CASS_BUILD_INTEGRATION_TESTS"] = False
        tc.variables["CASS_BUILD_SHARED"] = self.options.shared
        tc.variables["CASS_BUILD_STATIC"] = not self.options.shared
        tc.variables["CASS_BUILD_TESTS"] = False
        tc.variables["CASS_BUILD_UNIT_TESTS"] = False
        tc.variables["CASS_DEBUG_CUSTOM_ALLOC"] = False
        tc.variables["CASS_INSTALL_HEADER_IN_SUBDIR"] = self.options.install_header_in_subdir
        tc.variables["CASS_INSTALL_PKG_CONFIG"] = False

        if self.options.use_atomic == "boost":
            tc.variables["CASS_USE_BOOST_ATOMIC"] = True
            tc.variables["CASS_USE_STD_ATOMIC"] = False

        elif self.options.use_atomic == "std":
            tc.variables["CASS_USE_BOOST_ATOMIC"] = False
            tc.variables["CASS_USE_STD_ATOMIC"] = True
        else:
            tc.variables["CASS_USE_BOOST_ATOMIC"] = False
            tc.variables["CASS_USE_STD_ATOMIC"] = False

        tc.variables["CASS_USE_OPENSSL"] = self.options.with_openssl
        tc.variables["CASS_USE_STATIC_LIBS"] = False
        tc.variables["CASS_USE_ZLIB"] = self.options.with_zlib
        tc.variables["CASS_USE_LIBSSH2"] = False

        # FIXME: To use kerberos, its conan package is needed. Uncomment this when kerberos conan package is ready.
        # tc.variables["CASS_USE_KERBEROS"] = self.options.with_kerberos

        if self.settings.os == "Linux":
            tc.variables["CASS_USE_TIMERFD"] = self.options.use_timerfd
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE.txt", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(
                ["iphlpapi", "psapi", "wsock32", "crypt32", "ws2_32", "userenv", "version"]
            )
            if not self.options.shared:
                self.cpp_info.defines = ["CASS_STATIC"]
