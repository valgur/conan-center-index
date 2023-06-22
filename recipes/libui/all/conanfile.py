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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class libuiConan(ConanFile):
    name = "libui"
    description = "Simple and portable GUI library in C that uses the native GUI technologies of each platform it supports."
    topics = ("ui", "gui")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/andlabs/libui"
    license = "MIT"
    generators = "cmake", "pkg_config"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def requirements(self):
        self.requires("gtk/3.24.24")

    def generate(self):
        tc = CMakeToolchain(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)
        copy(self, pattern="*.h", dst="include", src=self.source_folder)
        copy(self, pattern="*.dll", dst="bin", keep_path=False)
        copy(self, pattern="*.lib", dst="lib", keep_path=False)
        copy(self, pattern="*.a", dst="lib", keep_path=False)
        copy(self, pattern="*.so*", dst="lib", keep_path=False)
        copy(self, pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(
                [
                    "user32",
                    "kernel32",
                    "gdi32",
                    "comctl32",
                    "msimg32",
                    "comdlg32",
                    "d2d1",
                    "dwrite",
                    "ole32",
                    "oleaut32",
                    "oleacc",
                    "uuid",
                    "windowscodecs",
                ]
            )
