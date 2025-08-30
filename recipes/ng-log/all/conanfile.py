import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NgLogConan(ConanFile):
    name = "ng-log"
    description = ("ng-log (formerly Google Logging Library or glog) is a C++14 library that implements application-level logging."
                   " The library provides logging APIs based on C++-style streams and various helper macros.")
    license = "BSD-3-Clause"
    homepage = "https://ng-log.github.io/ng-log/stable/"
    topics = ("logging", "glog")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "glog_compat": [True, False],
        "with_gflags": [True, False],
        "with_threads": [True, False],
        "with_unwind": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "glog_compat": True,
        "with_gflags": True,
        "with_threads": True,
        "with_unwind": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_unwind
        if Version(self.version) >= "0.9.0":
            del self.options.glog_compat

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.with_gflags:
            self.options["gflags"].shared = self.options.shared

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_gflags:
            self.requires("gflags/2.2.2", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("with_unwind"):
            self.requires("libunwind/[^1.8.0]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_COMPAT"] = self.options.get_safe("glog_compat", False)
        tc.variables["WITH_GFLAGS"] = self.options.with_gflags
        tc.variables["WITH_THREADS"] = self.options.with_threads
        tc.variables["WITH_PKGCONFIG"] = True
        if self.settings.os == "Emscripten":
            tc.variables["WITH_SYMBOLIZE"] = False
            tc.variables["HAVE_SYSCALL_H"] = False
            tc.variables["HAVE_SYS_SYSCALL_H"] = False
        else:
            tc.variables["WITH_SYMBOLIZE"] = True
        tc.variables["WITH_UNWIND"] = self.options.get_safe("with_unwind", False)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["WITH_GTEST"] = False
        tc.variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("libunwind", "cmake_file_name", "Unwind")
        deps.set_property("libunwind", "cmake_target_name", "unwind::unwind")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ng-log")
        self.cpp_info.components["ng-log_"].set_property("cmake_target_name", "ng-log::ng-log")
        self.cpp_info.components["ng-log_"].set_property("pkg_config_name", "libng-log")

        postfix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.components["ng-log_"].libs = ["ng-log" + postfix]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["ng-log_"].system_libs = ["pthread", "m", "dl"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["ng-log_"].system_libs = ["dbghelp"]
            self.cpp_info.components["ng-log_"].defines = ["NGLOG_NO_ABBREVIATED_SEVERITIES"]
        self.cpp_info.components["ng-log_"].defines.append("NGLOG_USE_EXPORT")
        if not self.options.shared:
            self.cpp_info.components["ng-log_"].defines.append("NGLOG_STATIC_DEFINE")
        if self.options.get_safe("with_unwind"):
            self.cpp_info.components["ng-log_"].requires.append("libunwind::libunwind")
        if self.options.with_gflags:
            self.cpp_info.components["ng-log_"].defines.append("NGLOG_USE_GFLAGS")
            self.cpp_info.components["ng-log_"].requires.append("gflags::gflags")

        if self.options.get_safe("glog_compat"):
            self.cpp_info.components["glog"].set_property("cmake_target_name", "glog::glog")
            self.cpp_info.components["glog"].set_property("pkg_config_name", "libglog")
            self.cpp_info.components["glog"].libs = ["glog" + postfix]
            if self.settings.os == "Windows":
                self.cpp_info.components["glog"].defines.append("GLOG_NO_ABBREVIATED_SEVERITIES")
            if not self.options.shared:
                self.cpp_info.components["glog"].defines.append("NGLOG_COMPAT_STATIC_DEFINE")
            if self.options.with_gflags and not self.options.shared:
                self.cpp_info.components["glog"].defines.extend(["GFLAGS_DLL_DECLARE_FLAG", "GFLAGS_DLL_DEFINE_FLAG"])
            self.cpp_info.components["glog"].defines.append("GLOG_USE_GLOG_EXPORT")
            self.cpp_info.components["glog"].requires = ["ng-log_"]
