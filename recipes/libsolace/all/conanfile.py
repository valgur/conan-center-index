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


class LibsolaceConan(ConanFile):
    name = "libsolace"
    description = "High performance components for mission critical applications"
    topics = ("HPC", "High reliability", "P10", "solace", "performance", "c++", "conan")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/abbyssoul/libsolace"
    license = "Apache-2.0"
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
    def _supported_cppstd(self):
        return ["17", "gnu17", "20", "gnu20"]

    def configure(self):
        compiler_version = Version(self, str(self.settings.compiler.version))

        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("This library is not yet compatible with Windows")
        # Exclude compilers that claims to support C++17 but do not in practice
        if (
            (self.settings.compiler == "gcc" and compiler_version < "7")
            or (self.settings.compiler == "clang" and compiler_version < "5")
            or (self.settings.compiler == "apple-clang" and compiler_version < "9")
        ):
            raise ConanInvalidConfiguration(
                "This library requires C++17 or higher support standard. {} {} is not supported".format(
                    self.settings.compiler, self.settings.compiler.version
                )
            )
        if self.settings.compiler.cppstd and not self.settings.compiler.cppstd in self._supported_cppstd:
            raise ConanInvalidConfiguration(
                "This library requires c++17 standard or higher. {} required".format(
                    self.settings.compiler.cppstd
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PKG_CONFIG"] = "OFF"
        tc.variables["SOLACE_GTEST_SUPPORT"] = "OFF"
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
        copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = ["solace"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("m")
