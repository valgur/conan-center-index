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
import glob
import os


class NanodbcConan(ConanFile):
    name = "nanodbc"
    description = "A small C++ wrapper for the native C ODBC API"
    topics = ("odbc", "database")
    license = "MIT"
    homepage = "https://github.com/nanodbc/nanodbc/"
    url = "https://github.com/conan-io/conan-center-index"
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
                "nanodbc requires c++14, but is unknown to this recipe. Assuming your compiler supports c++14."
            )

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
