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

required_conan_version = ">=1.40.0"


class OfeliConan(ConanFile):
    name = "ofeli"
    description = "An Object Finite Element Library"
    topics = ("finite-element", "finite-element-library", "finite-element-analysis", "finite-element-solver")
    license = "LGPL-3.0-or-later"
    homepage = "http://ofeli.org/index.html"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    _autotools = None

    @property
    def _doc_folder(self):
        return os.path.join(self.source_folder, "doc")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Ofeli is just supported for Linux")
        if self.settings.compiler != "gcc":
            raise ConanInvalidConfiguration("Ofeli is just supported for GCC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)
        if self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Ofeli supports only libstdc++'s new ABI")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        self._autotools.configure(
            args=["--enable-%s" % ("release" if self.settings.build_type == "Release" else "debug")]
        )
        return self._autotools

    def build(self):
        with chdir(self, self.source_folder):
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(
            self,
            "*libofeli.a",
            dst=os.path.join(self.package_folder, "lib"),
            src=os.path.join(self.source_folder, "src"),
        )
        copy(
            self,
            "*.md",
            dst=os.path.join(self.package_folder, "res"),
            src=os.path.join(self.source_folder, "material"),
        )
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self._doc_folder)

    def package_info(self):
        self.cpp_info.libs = ["ofeli"]
        self.env_info.OFELI_PATH_MATERIAL.append(os.path.join(self.package_folder, "res"))
