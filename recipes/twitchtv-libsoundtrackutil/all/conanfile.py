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
import os


class TwitchTvLibSoundtrackUtilConan(ConanFile):
    name = "twitchtv-libsoundtrackutil"
    license = "MIT"
    homepage = "https://github.com/twitchtv/libsoundtrackutil"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Twitch Soundtrack utility library"
    topics = ("twitch", "soundtrack")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _compilers_min_version(self):
        return {
            "gcc": "8",
            "clang": "8",
            "apple-clang": "10",
            "Visual Studio": "15",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("twitch-native-ipc/3.1.1")
        self.requires("ms-gsl/2.0.0")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 17)

        min_version = self._compilers_min_version.get(str(self.settings.compiler), False)
        if min_version:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(f"{self.name} requires C++17")
        else:
            self.output.warn("unknown compiler, assuming C++17 support")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(f"libsoundtrackutil-{self.version}", self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_CODE_FORMATTING"] = False
        tc.variables["BUILD_TESTING"] = False
        if self.settings.compiler == "Visual Studio":
            tc.variables["MSVC_DYNAMIC_RUNTIME"] = self.settings.compiler.runtime in ("MD", "MDd")
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"), recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["libsoundtrackutil"]

        if stdcpp_library(self):
            self.cpp_info.system_libs.append(stdcpp_library(self))
