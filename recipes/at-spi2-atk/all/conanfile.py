# Warnings:
#   Disallowed attribute 'generators = 'pkg_config''
#   Unexpected method '_configure_meson'
#   Missing required method 'generate'

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

required_conan_version = ">=1.53.0"


class AtSPI2AtkConan(ConanFile):
    name = "at-spi2-atk"
    description = "library that bridges ATK to At-Spi2 D-Bus service."
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.gnome.org/GNOME/at-spi2-atk"
    topics = ("atk", "accessibility")

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
    deprecated = "at-spi2-core"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("at-spi2-core/2.49.1")
        self.requires("atk/2.38.0")
        self.requires("glib/2.77.0")
        self.requires("libxml2/2.11.4")

    def validate(self):
        if self.settings.os not in ("Linux", "FreeBSD"):
            raise ConanInvalidConfiguration("at-spi2-atk is only supported on Linux and FreeBSD")
        if self.options.shared and (
            not self.dependencies["glib"].options.shared
            or not self.dependencies["at-spi2-core"].options.shared
            or not self.dependencies["atk"].options.shared
        ):
            raise ConanInvalidConfiguration(
                "Linking a shared library against static glib can cause unexpected behaviour."
            )

    def build_requirements(self):
        self.tool_requires("meson/1.2.0")
        self.tool_requires("pkgconf/1.9.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def _configure_meson(self):
        if self._meson:
            return self._meson
        self._meson = Meson(self)
        args = []
        args.append("--wrap-mode=nofallback")
        self._meson.configure(
            build_folder=self._build_subfolder,
            source_folder=self.source_folder,
            pkg_config_paths=".",
            args=args,
        )
        return self._meson

    def build(self):
        meson = self._configure_meson()
        meson.build()

    def package(self):
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        meson = self._configure_meson()
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libs = ["atk-bridge-2.0"]
        self.cpp_info.includedirs = [os.path.join("include", "at-spi2-atk", "2.0")]
        self.cpp_info.set_property("pkg_config_name", "atk-bridge-2.0")
