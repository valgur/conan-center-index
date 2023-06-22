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
required_conan_version = ">=1.33.0"


class CargsConan(ConanFile):
    name = "cargs"
    description = (
        "A lightweight getopt replacement that works on Linux, "
        "Windows and macOS. Command line argument parser library"
        " for C/C++. Can be used to parse argv and argc parameters."
    )
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"
    homepage = "https://likle.github.io/cargs/"
    topics = (
        "cargs",
        "cross-platform",
        "windows",
        "macos",
        "osx",
        "linux",
        "getopt",
        "getopt-long",
        "command-line-parser",
        "command-line",
        "arguments",
        "argument-parser",
    )
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], destination=self._source_subfolder, strip_root=True
        )

    def build(self):
        cmake = CMake(self)
        cmake.definitions["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = (
            self.options.shared and self.settings.os == "Windows"
        )
        cmake.configure(build_folder=self._build_subfolder)
        cmake.build(target="cargs")

    def package(self):
        include_dir = os.path.join(self._source_subfolder, "include")
        lib_dir = os.path.join(self._build_subfolder, "lib")
        bin_dir = os.path.join(self._build_subfolder, "bin")

        self.copy("LICENSE.md", dst="licenses", src=self._source_subfolder)
        self.copy("cargs.h", dst="include", src=include_dir)
        self.copy(pattern="*.a", dst="lib", src=lib_dir, keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src=lib_dir, keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", src=lib_dir, keep_path=False)
        self.copy(pattern="*.so*", dst="lib", src=lib_dir, keep_path=False, symlinks=True)
        self.copy(pattern="*.dll", dst="bin", src=bin_dir, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
