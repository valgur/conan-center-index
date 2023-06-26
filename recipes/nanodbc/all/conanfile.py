# TODO: verify the Conan v2 migration

import glob
import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class NanodbcConan(ConanFile):
    name = "nanodbc"
    description = "A small C++ wrapper for the native C ODBC API"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/nanodbc/nanodbc/"
    topics = ("odbc", "database")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "async": [True, False],
        "unicode": [True, False],
        "with_boost": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "async": True,
        "unicode": False,
        "with_boost": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    _compiler_cxx14 = {
        "gcc": 5,
        "clang": "3.4",
        "Visual Studio": 14,
        "apple-clang": "9.1",  # FIXME: wild guess
    }

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)
        _minimum_compiler = self._compiler_cxx14.get(str(self.settings.compiler))
        if _minimum_compiler:
            if Version(self.settings.compiler.version) < _minimum_compiler:
                raise ConanInvalidConfiguration(
                    "nanodbc requires c++14, which your compiler does not support"
                )
        else:
            self.output.warn(
                "nanodbc requires c++14, but is unknown to this recipe. "
                "Assuming your compiler supports c++14."
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_boost:
            self.requires("boost/1.76.0")
        if self.settings.os != "Windows":
            self.requires("odbc/2.3.9")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(glob.glob("nanodbc-*")[0], self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["NANODBC_DISABLE_ASYNC"] = not self.options.get_safe("async")
        tc.variables["NANODBC_ENABLE_UNICODE"] = self.options.unicode
        tc.variables["NANODBC_ENABLE_BOOST"] = self.options.with_boost
        tc.variables["NANODBC_DISABLE_LIBCXX"] = self.settings.get_safe("compiler.libcxx") != "libc++"
        tc.variables["NANODBC_DISABLE_INSTALL"] = False
        tc.variables["NANODBC_DISABLE_EXAMPLES"] = True
        tc.variables["NANODBC_DISABLE_TESTS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = ["nanodbc"]
        if not self.options.shared:
            if self.settings.os == "Windows":
                self.cpp_info.system_libs = ["odbc32"]
