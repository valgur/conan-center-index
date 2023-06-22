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


class GetDnsConan(ConanFile):
    name = "getdns"
    description = "A modern asynchronous DNS API"
    topics = ("asynchronous", "event")
    license = "BSD-3-Clause"
    homepage = "https://getdnsapi.net/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "CMakeLists.txt", "patches/**"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tls": [False, "gnutls"],
        "stub_only": ["auto", True, False],
        "with_libev": ["auto", True, False],
        "with_libevent": [True, False],
        "with_libuv": [True, False],
        "with_libidn2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "stub_only": "auto",
        "tls": False,
        "with_libev": "auto",
        "with_libevent": True,
        "with_libuv": True,
        "with_libidn2": True,
    }
    generators = "cmake", "pkg_config", "cmake_find_package"

    @property
    def _with_libev(self):
        if self.options.with_libev == "auto":
            return self.settings.os != "Windows"
        else:
            return self.options.with_libev

    @property
    def _stub_only(self):
        if self.options.stub_only == "auto":
            # FIXME: uncomment the next line when libunbound is available
            # return self.settings.os == "Windows"
            return True
        else:
            return self.options.stub_only

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        self.requires("openssl/1.1.1j")
        if self._with_libev:
            self.requires("libev/4.33")
        if self.options.with_libevent:
            self.requires("libevent/2.1.12")
        if self.options.with_libuv:
            self.requires("libuv/1.41.0")
        if self.options.with_libidn2:
            self.requires("libidn2/2.3.0")
        if self.options.tls == "gnutls":
            self.requires("nettle/3.6")
            # FIXME: missing gnutls recipe
            raise ConanInvalidConfiguration("gnutls is not (yet) available on cci")
        if not self._stub_only:
            # FIXME: missing libunbound recipe
            raise ConanInvalidConfiguration("libunbound is not (yet) available on cci")

    def build_requirements(self):
        self.build_requires("pkgconf/1.7.3")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("getdns-{}".format(self.version), self._source_subfolder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OPENSSL_USE_STATIC_LIBS"] = not self.options["openssl"].shared
        tc.variables["ENABLE_SHARED"] = self.options.shared
        tc.variables["ENABLE_STATIC"] = not self.options.shared
        tc.variables["ENABLE_STUB_ONLY"] = self._stub_only
        tc.variables["BUILD_LIBEV"] = self._with_libev
        tc.variables["BUILD_LIBEVENT2"] = self.options.with_libevent
        tc.variables["BUILD_LIBUV"] = self.options.with_libuv
        tc.variables["USE_LIBIDN2"] = self.options.with_libidn2
        tc.variables["USE_GNUTLS"] = self.options.tls == "gnutls"
        tc.variables["BUILD_TESTING"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        # Use FindOpenSSL.cmake to let check_function_exists succeed
        # Remove other cmake modules as they use FindPkgConfig
        for fn in glob.glob("Find*cmake"):
            if "OpenSSL" not in fn:
                os.unlink(fn)
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_id(self):
        self.info.options.stub_only = self._stub_only
        self.info.options.with_libev = self._with_libev

    def package_info(self):
        libsuffix = ""
        if self.settings.compiler == "Visual Studio" and not self.options.shared:
            libsuffix = "_static"

        self.cpp_info.components["libgetdns"].libs = ["getdns" + libsuffix]
        self.cpp_info.components["libgetdns"].includedirs.append(os.path.join("include", "getdns"))
        self.cpp_info.components["libgetdns"].names["pkg_config"] = "getdns"
        self.cpp_info.components["libgetdns"].requires = ["openssl::openssl"]
        if self.options.with_libidn2:
            self.cpp_info.components["libgetdns"].requires.append("libidn2::libidn2")
        if self.options.with_libidn2:
            self.cpp_info.components["libgetdns"].requires.append("libidn2::libidn2")
        if self.options.tls == "gnutls":
            self.cpp_info.components["libgetdns"].requires.extend(["nettle::nettle", "gnutls::gnutls"])

        if self.options.with_libevent:
            self.cpp_info.components["dns_ex_event"].libs = ["getdns_ex_event" + libsuffix]
            self.cpp_info.components["dns_ex_event"].requires = ["libgetdns", "libevent::libevent"]
            self.cpp_info.components["dns_ex_event"].names["pkg_config"] = "getdns_ext_event"

        if self._with_libev:
            self.cpp_info.components["dns_ex_ev"].libs = ["getdns_ex_ev" + libsuffix]
            self.cpp_info.components["dns_ex_ev"].requires = ["libgetdns", "libev::libev"]
            self.cpp_info.components["dns_ex_ev"].names["pkg_config"] = "getdns_ext_ev"

        if self.options.with_libuv:
            self.cpp_info.components["dns_ex_uv"].libs = ["getdns_ex_uv" + libsuffix]
            self.cpp_info.components["dns_ex_uv"].requires = ["libgetdns", "libuv::libuv"]
            self.cpp_info.components["dns_ex_uv"].names["pkg_config"] = "getdns_ext_uv"

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
