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
import os
import shutil


class PangommConan(ConanFile):
    name = "pangomm"
    homepage = "https://gitlab.gnome.org/GNOME/pangomm"
    license = "LGPL-2.1"
    url = "https://github.com/conan-io/conan-center-index"
    description = "pangomm is a C++ API for Pango: a library for layout and rendering of text."
    topics = ["pango", "wrapper", "text rendering", "fonts", "freedesktop"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    generators = "pkg_config"
    exports_sources = "patches/**"

    @property
    def _is_2_48_api(self):
        return Version(self.version) >= "2.48.0"

    @property
    def _is_1_4_api(self):
        return Version(self.version) >= "1.4.0" and Version(self.version) < "2.48.0"

    @property
    def _api_version(self):
        return "2.48" if self._is_2_48_api else "1.4"

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration("Cross-building not implemented")

        if self.settings.compiler.get_safe("cppstd"):
            if self._is_2_48_api:
                check_min_cppstd(self, 17)
            elif self._is_1_4_api:
                check_min_cppstd(self, 11)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def build_requirements(self):
        self.build_requires("meson/0.59.1")
        self.build_requires("pkgconf/1.7.4")

    def requirements(self):
        self.requires("pango/1.50.7")

        # FIXME: temporary fix for dependency versions mismatch
        # once dependencies versions are bumped remove these requirements
        self.requires("expat/2.4.8")
        self.requires("zlib/1.2.12")
        self.requires("glib/2.72.1")

        if self._is_2_48_api:
            self.requires("glibmm/2.72.1")
            self.requires("cairomm/1.16.1")
        elif self._is_1_4_api:
            self.requires("glibmm/2.66.4")
            self.requires("cairomm/1.14.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

        # glibmm_generate_extra_defs library does not provide any standard way
        # for discovery, which is why pangomm uses "find_library" method instead
        # of "dependency". this patch adds a hint to where this library is
        glibmm_generate_extra_defs_dir = [
            os.path.join(self.deps_cpp_info["glibmm"].rootpath, libdir)
            for libdir in self.deps_cpp_info["glibmm"].libdirs
        ]

        replace_in_file(
            self,
            os.path.join(self.source_folder, "tools", "extra_defs_gen", "meson.build"),
            "required: glibmm_dep.type_name() != 'internal',",
            f"required: glibmm_dep.type_name() != 'internal', dirs: {glibmm_generate_extra_defs_dir}",
        )

        if is_msvc(self):
            # when using cpp_std=c++NM the /permissive- flag is added which
            # attempts enforcing standard conformant c++ code
            # the problem is that older versions of Windows SDK is not standard
            # conformant! see:
            # https://developercommunity.visualstudio.com/t/error-c2760-in-combaseapih-with-windows-sdk-81-and/185399
            replace_in_file(
                self, os.path.join(self.source_folder, "meson.build"), "cpp_std=c++", "cpp_std=vc++"
            )

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def build(self):
        self._patch_sources()
        with environment_append(self, RunEnvironment(self).vars):
            meson = self._configure_meson()
            meson.build()

    def _configure_meson(self):
        meson = Meson(self)
        defs = {
            "build-documentation": "false",
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
        copy(self, "COPYING", dst="licenses", src=self.source_folder)
        meson = self._configure_meson()
        meson.install()

        shutil.move(
            os.path.join(
                self.package_folder, "lib", f"pangomm-{self._api_version}", "include", "pangommconfig.h"
            ),
            os.path.join(self.package_folder, "include", f"pangomm-{self._api_version}", "pangommconfig.h"),
        )

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pangomm-{self._api_version}", "include"))

        if is_msvc(self):
            rm(self, "*.pdb", os.path.join(self.package_folder, "bin"), recursive=True)
            if not self.options.shared:
                rename(
                    self,
                    os.path.join(self.package_folder, "lib", f"libpangomm-{self._api_version}.a"),
                    os.path.join(self.package_folder, "lib", f"pangomm-{self._api_version}.lib"),
                )

    def package_info(self):
        pangomm_lib = f"pangomm-{self._api_version}"
        glibmm_lib = "glibmm::glibmm-2.68" if self._is_2_48_api else "glibmm::glibmm-2.4"
        giomm_lib = "glibmm::giomm-2.68" if self._is_2_48_api else "glibmm::giomm-2.4"
        cairomm_lib = "cairomm::cairomm-1.16" if self._is_2_48_api else "cairomm::cairomm-1.0"

        self.cpp_info.components[pangomm_lib].names["pkg_config"] = pangomm_lib
        self.cpp_info.components[pangomm_lib].libs = [pangomm_lib]
        self.cpp_info.components[pangomm_lib].includedirs = [os.path.join("include", pangomm_lib)]
        self.cpp_info.components[pangomm_lib].requires = [
            "pango::pangocairo",
            glibmm_lib,
            giomm_lib,
            cairomm_lib,
        ]
        self.cpp_info.components[pangomm_lib].set_property(
            "pkg_config_custom_content", f"gmmprocm4dir=${{libdir}}/{pangomm_lib}/proc/m4"
        )

        # FIXME: remove once dependency mismatch issues are solved
        self.cpp_info.components[pangomm_lib].requires.extend(
            ["expat::expat", "zlib::zlib", "glib::glib-2.0"]
        )
