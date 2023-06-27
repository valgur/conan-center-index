from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get, replace_in_file, rmdir
from conan.tools.scm import Version
import os

required_conan_version = ">=1.54.0"


class IXWebSocketConan(ConanFile):
    name = "ixwebsocket"
    description = "IXWebSocket is a C++ library for WebSocket client and server development"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/machinezone/IXWebSocket"
    topics = ("socket", "websocket")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tls": ["mbedtls", "openssl", "applessl", False],
        "with_zlib": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tls": "mbedtls",
        "with_zlib": True,
    }

    @property
    def _min_cppstd(self):
        # After version 11.0.8, IXWebSocket is fully compatible with C++ 11.
        # https://github.com/machinezone/IXWebSocket/commit/ee5a2eb46ee0e109415dc02b0db85a9c76256090
        return "14" if Version(self.version) < "11.0.8" else "11"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "10.1.5":
            # zlib is always required before 10.1.5
            self.options.rm_safe("with_zlib")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("with_zlib", True):
            self.requires("zlib/1.2.13")
        if self.options.tls == "openssl":
            self.requires("openssl/1.1.1s")
        elif self.options.tls == "mbedtls":
            self.requires("mbedtls/2.25.0")

    @property
    def _can_use_openssl(self):
        if self.settings.os == "Windows":
            # Future: support for OpenSSL on Windows was introduced in 7.9.3. Earlier versions force MbedTLS
            return Version(self.version) >= "7.9.3"
        # The others do, by default, support OpenSSL and MbedTLS. Non-standard operating systems might
        # be a challenge.
        # Older versions doesn't support OpenSSL on Mac, but those are unlikely to be built now.
        return True

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)
        if self.options.tls == "applessl" and not is_apple_os(self):
            raise ConanInvalidConfiguration("Can only use Apple SSL on Apple.")
        elif not self._can_use_openssl and self.options.tls == "openssl":
            raise ConanInvalidConfiguration(
                f"{self.ref} doesn't support OpenSSL with Windows; use v7.9.3 or newer for this to be valid"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_TLS"] = bool(self.options.tls)
        tc.variables["USE_MBED_TLS"] = self.options.tls == "mbedtls"
        tc.variables["USE_OPEN_SSL"] = self.options.tls == "openssl"
        # Apple configures itself if USE_TLS True, and USE_MBED_TLS + USE_OPEN_SSL False
        if Version(self.version) >= "10.1.5":
            tc.variables["USE_ZLIB"] = self.options.with_zlib
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        # Use CMake variables from MbedTLSConfig.cmake generated by conan
        replace_in_file(self, cmakelists, "${MBEDTLS_INCLUDE_DIRS}", "${MbedTLS_INCLUDE_DIRS}")
        replace_in_file(self, cmakelists, "${MBEDTLS_LIBRARIES}", "MbedTLS::mbedtls")
        # Do not force PIC
        if Version(self.version) >= "9.5.7":
            replace_in_file(self, cmakelists, "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        # Allow shared
        if Version(self.version) < "11.1.4":
            replace_in_file(self, cmakelists, "add_library( ixwebsocket STATIC", "add_library( ixwebsocket")
        if Version(self.version) < "9.8.5":
            replace_in_file(
                self,
                cmakelists,
                "ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}/lib",
                (
                    "ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}/lib LIBRARY DESTINATION lib RUNTIME"
                    " DESTINATION bin"
                ),
            )
        elif Version(self.version) < "11.4.3":
            replace_in_file(
                self,
                cmakelists,
                "ARCHIVE DESTINATION lib",
                "ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin",
            )
        else:
            replace_in_file(
                self,
                cmakelists,
                "ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}",
                (
                    "ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR} LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}"
                    " RUNTIME DESTINATION bin"
                ),
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ixwebsocket")
        self.cpp_info.set_property("cmake_target_name", "ixwebsocket::ixwebsocket")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["wsock32", "ws2_32", "shlwapi"])
            if bool(self.options.tls):
                self.cpp_info.system_libs.append("crypt32")
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
        if self.options.get_safe("with_zlib", False):
            self.cpp_info.defines.append("IXWEBSOCKET_USE_ZLIB")
        if self.options.tls == "mbedtls":
            self.cpp_info.defines.append("IXWEBSOCKET_USE_MBED_TLS")
        elif self.options.tls == "openssl":
            self.cpp_info.defines.append("IXWEBSOCKET_USE_OPEN_SSL")
        elif self.options.tls == "applessl":
            self.cpp_info.frameworks = ["Security", "CoreFoundation"]
            self.cpp_info.defines.append("IXWEBSOCKET_USE_SECURE_TRANSPORT")
