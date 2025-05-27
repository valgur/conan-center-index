import os

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NsyncConan(ConanFile):
    name = "nsync"
    homepage = "https://github.com/google/nsync"
    description = "Library that exports various synchronization primitives"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("c", "thread", "multithreading", "google")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set (CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required (VERSION 2.8.12)",
                        "cmake_minimum_required (VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NSYNC_ENABLE_TESTS"] = False
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

    def _patch_sources(self):
        if self.settings.os == "Windows" and self.options.shared:
            ar_dest = "ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR} COMPONENT Development"
            rt_dest = 'RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"'
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                            f"{ar_dest})",
                            f"{ar_dest}\n{rt_dest})")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.components["nsync_c"].libs = ["nsync"]
        self.cpp_info.components["nsync_cpp"].libs = ["nsync_cpp"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["nsync_c"].system_libs.append("pthread")
            self.cpp_info.components["nsync_cpp"].system_libs.extend(["m", "pthread"])
