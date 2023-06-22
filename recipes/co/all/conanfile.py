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

required_conan_version = ">=1.33.0"


class CoConan(ConanFile):
    name = "co"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/idealvin/co"
    license = "MIT"
    description = "A go-style coroutine library in C++11 and more."
    topics = ("coroutine", "c++11")

    deprecated = "cocoyaxi"

    exports_sources = "CMakeLists.txt", "patches/*"
    generators = "cmake", "cmake_find_package"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libcurl": [True, False],
        "with_openssl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libcurl": False,
        "with_openssl": False,
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

    def requirements(self):
        if self.options.with_libcurl:
            self.requires("libcurl/7.79.1")
        if self.options.with_openssl:
            self.requires("openssl/1.1.1l")

    def build_requirements(self):
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            #  The OSX_ARCHITECTURES target property is now respected for the ASM language
            self.build_requires("cmake/3.20.1")

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder
        )

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def generate(self):
        tc = CMakeToolchain(self)
        if not self.options.shared:
            tc.variables["FPIC"] = self.options.get_safe("fPIC", False)
        runtime = self.settings.get_safe("compiler.runtime")
        if runtime:
            tc.variables["STATIC_VS_CRT"] = "MT" in runtime
        tc.variables["WITH_LIBCURL"] = self.options.with_libcurl
        tc.variables["WITH_OPENSSL"] = self.options.with_openssl
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("LICENSE.md", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["co"]
        self.cpp_info.names["cmake_find_package"] = "co"
        self.cpp_info.names["cmake_find_package_multi"] = "co"

    def validate(self):
        if self.options.with_libcurl:
            if not self.options.with_openssl:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires with_openssl=True when using with_libcurl=True"
                )
            if self.options["libcurl"].with_ssl != "openssl":
                raise ConanInvalidConfiguration(
                    f"{self.name} requires libcurl:with_ssl='openssl' to be enabled"
                )
            if not self.options["libcurl"].with_zlib:
                raise ConanInvalidConfiguration(f"{self.name} requires libcurl:with_zlib=True to be enabled")
