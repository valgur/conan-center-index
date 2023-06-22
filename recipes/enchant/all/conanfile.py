# TODO: verify the Conan v2 migration

import functools
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

required_conan_version = ">=1.43.0"


class EnchantConan(ConanFile):
    name = "enchant"
    description = (
        "Enchant aims to provide a simple but comprehensive abstraction for "
        "dealing with different spell checking libraries in a consistent way"
    )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://abiword.github.io/enchant/"
    topics = ("enchant", "spell", "spell-check")
    license = "LGPL-2.1-or-later"
    settings = "os", "arch", "compiler", "build_type"
    requires = "glib/2.71.3", "hunspell/1.7.0"

    def export_sources(self):
        copy(self, "CMakeLists.txt")
        copy(self, "configmake.h")
        copy(self, "configure.cmake")
        export_conandata_patches(self)

    def source(self):
        root = self.source_folder
        get_args = self.conan_data["sources"][self.version]
        get(self, **get_args, destination=root, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CONAN_enchant_VERSION"] = self.version
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.LIB", "licenses", self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["enchant"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
