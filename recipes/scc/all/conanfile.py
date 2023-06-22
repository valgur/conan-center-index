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
from conan.errors import ConanInvalidConfiguration
import functools

required_conan_version = ">=1.50.0"


class SystemcComponentsConan(ConanFile):
    name = "scc"
    description = """A light weight productivity library for SystemC and TLM 2.0"""
    homepage = "https://minres.github.io/SystemC-Components"
    url = "https://github.com/conan-io/conan-center-index"
    license = "Apache-2.0"
    topics = ("systemc", "modeling", "tlm", "scc")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fPIC": [True, False],
        "enable_phase_callbacks": [True, False],
        "enable_phase_callbacks_tracing": [True, False],
    }
    default_options = {
        "fPIC": True,
        "enable_phase_callbacks": False,
        "enable_phase_callbacks_tracing": False,
    }

    # no exports_sources attribute, but export_sources(self) method instead
    # this allows finer grain exportation of patches per version
    def export_sources(self):
        copy(self, "CMakeLists.txt")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.settings.os == "Macos":
            raise ConanInvalidConfiguration(f"{self.name} is not suppported on {self.settings.os}.")
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "7":
            raise ConanInvalidConfiguration("GCC < version 7 is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build_requirements(self):
        self.tool_requires("cmake/3.24.0")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SC_WITH_PHASE_CALLBACKS"] = self.options.enable_phase_callbacks
        tc.variables["SC_WITH_PHASE_CALLBACK_TRACING"] = self.options.enable_phase_callbacks_tracing
        tc.variables["BUILD_SCC_DOCUMENTATION"] = False
        tc.variables["SCC_LIB_ONLY"] = True
        if self.settings.os == "Windows":
            tc.variables["SCC_LIMIT_TRACE_TYPE_LIST"] = True

    def build(self):
        cmake = CMake(self)

    def package(self):
        copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["busses"].libs = ["busses"]
        self.cpp_info.components["scc-sysc"].libs = ["scc-sysc"]
        self.cpp_info.components["scc-util"].libs = ["scc-util"]
        self.cpp_info.components["scv-tr"].libs = ["scv-tr"]
        self.cpp_info.components["tlm-interfaces"].libs = ["tlm-interfaces"]
