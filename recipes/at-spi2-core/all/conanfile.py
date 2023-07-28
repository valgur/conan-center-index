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


class AtSpi2CoreConan(ConanFile):
    name = "at-spi2-core"
    description = (
        "It provides a Service Provider Interface for the Assistive Technologies available on the GNOME"
        " platform and a library against which applications can be linked"
    )
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.gnome.org/GNOME/at-spi2-core/"
    topics = ("atk", "accessibility")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_x11": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_x11": False,
    }
    deprecated = "Consumers should migrate to at-spi2-core/[>=2.45.1], which includes atk and at-spi2-atk"

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("glib/2.77.0")
        if self.options.with_x11:
            self.requires("xorg/system")
        self.requires("dbus/1.15.6")

    def validate(self):
        if self.options.shared and not self.dependencies["glib"].options.shared:
            raise ConanInvalidConfiguration(
                "Linking a shared library against static glib can cause unexpected behaviour."
            )
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("only linux is supported by this recipe")

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
        defs = {}
        defs["introspection"] = "no"
        defs["docs"] = "false"
        defs["x11"] = "yes" if self.options.with_x11 else "no"
        args = []
        args.append("--datadir=%s" % os.path.join(self.package_folder, "res"))
        args.append("--localedir=%s" % os.path.join(self.package_folder, "res"))
        args.append("--wrap-mode=nofallback")
        self._meson.configure(
            defs=defs,
            build_folder=self._build_subfolder,
            source_folder=self.source_folder,
            pkg_config_paths=".",
            args=args,
        )
        return self._meson

    def build(self):
        apply_conandata_patches(self)
        if Version(self.version) >= "2.42.0":
            replace_in_file(
                self,
                os.path.join(self.source_folder, "bus", "meson.build"),
                "if x11_dep.found()",
                "if x11_option == 'yes'",
            )
        meson = self._configure_meson()
        meson.build()

    def package(self):
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        meson = self._configure_meson()
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "etc"))

    def package_info(self):
        self.cpp_info.libs = ["atspi"]
        self.cpp_info.includedirs = ["include/at-spi-2.0"]
        self.cpp_info.set_property("pkg_config_name", "atspi-2")
