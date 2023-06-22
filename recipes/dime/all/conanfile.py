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
from conan.tools.microsoft import is_msvc
import os
import functools
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class DimeConan(ConanFile):
    name = "dime"
    description = "DXF (Data eXchange Format) file format support library."
    topics = ("dxf", "coin3d", "opengl", "graphics")
    homepage = "https://github.com/coin3d/dime"
    url = "https://github.com/conan-io/conan-center-index"
    license = "BSD-3-Clause"
    generators = ("cmake",)
    settings = ("os", "arch", "compiler", "build_type")
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "fixbig": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "fixbig": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DIME_BUILD_SHARED_LIBS"] = self.options.shared
        if self.options.fixbig:
            tc.variables["CMAKE_CXX_FLAGS"] = "-DDIME_FIXBIG"

    def build(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "configure_file(${CMAKE_SOURCE_DIR}/${PROJECT_NAME_LOWER}.pc.cmake.in ${CMAKE_BINARY_DIR}/${PROJECT_NAME_LOWER}.pc @ONLY)",
            "configure_file(${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME_LOWER}.pc.cmake.in ${CMAKE_BINARY_DIR}/${PROJECT_NAME_LOWER}.pc @ONLY)",
        )
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if self.settings.os == "Windows" and is_msvc(self):
            rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        libname = "dime"
        if self.settings.os == "Windows" and is_msvc(self):
            libname = "{}{}{}{}".format(
                libname,
                Version(self.version).major,
                "" if self.options.shared else "s",
                "d" if self.settings.build_type == "Debug" else "",
            )
        self.cpp_info.libs = [libname]

        if self.settings.os == "Windows":
            self.cpp_info.cxxflags.append("-DDIME_DLL" if self.options.shared else "-DDIME_NOT_DLL")
        if self.options.fixbig:
            self.cpp_info.cxxflags.append("-DDIME_FIXBIG")

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
