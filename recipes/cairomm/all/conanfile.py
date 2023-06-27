# Warnings:
#   Unexpected method '_abi_version'
#   Unexpected method '_configure_meson'

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
from conan.tools.scm import Version
from conan.tools.system import package_manager
import glob
import os
import shutil

required_conan_version = ">=1.53.0"


class CairommConan(ConanFile):
    name = "cairomm"
    description = "cairomm is a C++ wrapper for the cairo graphics library."
    license = "LGPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/freedesktop/cairomm"
    topics = ["cairo", "wrapper", "graphics"]
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.shared:
            self.options["cairo"].shared = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cairo/1.17.4")

        if self._abi_version() == "1.16":
            self.requires("libsigcpp/3.0.7")
        else:
            self.requires("libsigcpp/2.10.8")

    def package_id(self):
        self.info.requires["cairo"].full_package_mode()

    def _abi_version(self):
        return "1.16" if Version(self.version) >= "1.16.0" else "1.0"

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration("Cross-building not implemented")
        if self.settings.compiler.get_safe("cppstd"):
            if self._abi_version() == "1.16":
                check_min_cppstd(self, 17)
            else:
                check_min_cppstd(self, 11)
        if self.options.shared and not self.options["cairo"].shared:
            raise ConanInvalidConfiguration(
                "Linking against static cairo would cause shared cairomm to link "
                "against static glib which can cause problems."
            )

    def build_requirements(self):
        self.build_requires("meson/0.59.1")
        self.build_requires("pkgconf/1.7.4")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = PkgConfigDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            # when using cpp_std=c++11 the /permissive- flag is added which
            # attempts enforcing standard conformant c++ code
            # the problem is that older versions of Windows SDK is not standard
            # conformant! see:
            # https://developercommunity.visualstudio.com/t/error-c2760-in-combaseapih-with-windows-sdk-81-and/185399
            replace_in_file(
                self, os.path.join(self.source_folder, "meson.build"), "cpp_std=c++", "cpp_std=vc++"
            )

    def build(self):
        self._patch_sources()
        with environment_append(self, RunEnvironment(self).vars):
            meson = self._configure_meson()
            meson.build()

    def _configure_meson(self):
        meson = Meson(self)
        defs = {
            "build-examples": "false",
            "build-documentation": "false",
            "build-tests": "false",
            "msvc14x-parallel-installable": "false",
            "default_library": "shared" if self.options.shared else "static",
        }
        meson.configure(
            defs=defs,
            build_folder=self._build_subfolder,
            source_folder=self.source_folder,
            pkg_config_paths=[self.install_folder],
        )
        return meson

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        meson = self._configure_meson()
        meson.install()
        if is_msvc(self):
            rm(self, "*.pdb", os.path.join(self.package_folder, "bin"), recursive=True)
            if not self.options.shared:
                rename(
                    self,
                    os.path.join(self.package_folder, "lib", f"libcairomm-{self._abi_version()}.a"),
                    os.path.join(self.package_folder, "lib", f"cairomm-{self._abi_version()}.lib"),
                )

        for header_file in glob.glob(
            os.path.join(self.package_folder, "lib", f"cairomm-{self._abi_version()}", "include", "*.h")
        ):
            shutil.move(
                header_file,
                os.path.join(
                    self.package_folder,
                    "include",
                    f"cairomm-{self._abi_version()}",
                    os.path.basename(header_file),
                ),
            )

        for dir_to_remove in ["pkgconfig", f"cairomm-{self._abi_version()}"]:
            rmdir(self, os.path.join(self.package_folder, "lib", dir_to_remove))

    def package_info(self):
        if self._abi_version() == "1.16":
            self.cpp_info.components["cairomm-1.16"].names["pkg_config"] = "cairomm-1.16"
            self.cpp_info.components["cairomm-1.16"].includedirs = [os.path.join("include", "cairomm-1.16")]
            self.cpp_info.components["cairomm-1.16"].libs = ["cairomm-1.16"]
            self.cpp_info.components["cairomm-1.16"].requires = ["libsigcpp::sigc++", "cairo::cairo_"]
            if is_apple_os(self.settings.os):
                self.cpp_info.components["cairomm-1.16"].frameworks = ["CoreFoundation"]
        else:
            self.cpp_info.components["cairomm-1.0"].names["pkg_config"] = "cairomm-1.0"
            self.cpp_info.components["cairomm-1.0"].includedirs = [os.path.join("include", "cairomm-1.0")]
            self.cpp_info.components["cairomm-1.0"].libs = ["cairomm-1.0"]
            self.cpp_info.components["cairomm-1.0"].requires = ["libsigcpp::sigc++-2.0", "cairo::cairo_"]
            if is_apple_os(self.settings.os):
                self.cpp_info.components["cairomm-1.0"].frameworks = ["CoreFoundation"]
