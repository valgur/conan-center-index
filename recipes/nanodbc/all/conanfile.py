import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NanodbcConan(ConanFile):
    name = "nanodbc"
    description = "A small C++ wrapper for the native C ODBC API"
    topics = ("odbc", "database")
    license = "MIT"
    homepage = "https://github.com/nanodbc/nanodbc/"
    url = "https://github.com/conan-io/conan-center-index"
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
        "with_boost": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_boost:
            self.requires("boost/[^1.71.0]")
        if self.settings.os != "Windows":
            self.requires("odbc/[^2.3.11]")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # No warnings as errors
        replace_in_file(self, "CMakeLists.txt", "-Werror", "")
        # CMake v4 support
        if Version(self.version) <= "2.14":
            replace_in_file(self, "CMakeLists.txt",
                            "cmake_minimum_required(VERSION 3.0.0)",
                            "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["NANODBC_DISABLE_ASYNC"] = not self.options.get_safe("async")
        tc.cache_variables["NANODBC_ENABLE_UNICODE"] = self.options.unicode
        tc.cache_variables["NANODBC_ENABLE_BOOST"] = self.options.with_boost
        tc.cache_variables["NANODBC_DISABLE_LIBCXX"] = self.settings.get_safe("compiler.libcxx") != "libc++"
        tc.cache_variables["NANODBC_DISABLE_INSTALL"] = False
        tc.cache_variables["NANODBC_DISABLE_EXAMPLES"] = True
        tc.cache_variables["NANODBC_DISABLE_TESTS"] = True
        tc.cache_variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nanodbc")
        self.cpp_info.set_property("cmake_target_name", "nanodbc::nanodbc")
        self.cpp_info.libs = ["nanodbc"]

        if not self.options.shared and self.settings.os == "Windows":
            self.cpp_info.system_libs = ["odbc32"]
