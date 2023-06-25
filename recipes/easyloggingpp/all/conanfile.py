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


required_conan_version = ">=1.33.0"


class EasyloggingppConan(ConanFile):
    name = "easyloggingpp"
    license = "The MIT License (MIT)"
    homepage = "https://github.com/amrayn/easyloggingpp"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Single header C++ logging library."
    topics = ("logging", "stacktrace", "efficient-logging")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "enable_crash_log": [True, False],
        "enable_thread_safe": [True, False],
        "enable_debug_errors": [True, False],
        "enable_default_logfile": [True, False],
        "disable_logs": [True, False],
        "disable_debug_logs": [True, False],
        "disable_info_logs": [True, False],
        "disable_warning_logs": [True, False],
        "disable_error_logs": [True, False],
        "disable_fatal_logs": [True, False],
        "disable_verbose_logs": [True, False],
        "disable_trace_logs": [True, False],
    }
    default_options = {
        "enable_crash_log": False,
        "enable_thread_safe": False,
        "enable_debug_errors": False,
        "enable_default_logfile": True,
        "disable_logs": False,
        "disable_debug_logs": False,
        "disable_info_logs": False,
        "disable_warning_logs": False,
        "disable_error_logs": False,
        "disable_fatal_logs": False,
        "disable_verbose_logs": False,
        "disable_trace_logs": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["build_static_lib"] = True
        tc.variables["enable_crash_log"] = self.options.enable_crash_log
        tc.variables["enable_thread_safe"] = self.options.enable_thread_safe
        tc.variables["enable_debug_errors"] = self.options.enable_debug_errors
        tc.variables["enable_default_logfile"] = self.options.enable_default_logfile
        tc.variables["disable_logs"] = self.options.disable_logs
        tc.variables["disable_debug_logs"] = self.options.disable_debug_logs
        tc.variables["disable_info_logs"] = self.options.disable_info_logs
        tc.variables["disable_warning_logs"] = self.options.disable_warning_logs
        tc.variables["disable_error_logs"] = self.options.disable_error_logs
        tc.variables["disable_fatal_logs"] = self.options.disable_fatal_logs
        tc.variables["disable_verbose_logs"] = self.options.disable_verbose_logs
        tc.variables["disable_trace_logs"] = self.options.disable_trace_logs
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "easyloggingpp"
        self.cpp_info.names["cmake_find_package_multi"] = "easyloggingpp"
        self.cpp_info.libs = ["easyloggingpp"]
        if self.options.enable_crash_log:
            self.cpp_info.defines.append("ELPP_FEATURE_CRASH_LOG")
        if self.options.enable_thread_safe:
            self.cpp_info.defines.append("ELPP_THREAD_SAFE")
        if self.options.enable_debug_errors:
            self.cpp_info.defines.append("ELPP_DEBUG_ERRORS")
        if self.options.enable_default_logfile:
            self.cpp_info.defines.append("ELPP_NO_DEFAULT_LOG_FILE")
        if self.options.disable_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_LOGS")
        if self.options.disable_debug_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_DEBUG_LOGS")
        if self.options.disable_info_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_INFO_LOGS")
        if self.options.disable_warning_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_WARNING_LOGS")
        if self.options.disable_error_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_ERROR_LOGS")
        if self.options.disable_fatal_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_FATAL_LOGS")
        if self.options.disable_verbose_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_VERBOSE_LOGS")
        if self.options.disable_trace_logs:
            self.cpp_info.defines.append("ELPP_DISABLE_TRACE_LOGS")
