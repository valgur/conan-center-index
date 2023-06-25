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
import shutil
import glob

required_conan_version = ">=1.36.0"


class GobjectIntrospectionConan(ConanFile):
    name = "gobject-introspection"
    description = "GObject introspection is a middleware layer between C libraries (using GObject) and language bindings"
    topics = "gobject-instrospection"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.gnome.org/GNOME/gobject-introspection"
    license = "LGPL-2.1"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    generators = "pkg_config"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "%s recipe does not support windows. Contributions are welcome!" % self.name
            )

    def build_requirements(self):
        if Version(self.version) >= "1.71.0":
            self.build_requires("meson/0.62.2")
        else:
            # https://gitlab.gnome.org/GNOME/gobject-introspection/-/issues/414
            self.build_requires("meson/0.59.3")
        self.build_requires("pkgconf/1.7.4")
        if self.settings.os == "Windows":
            self.build_requires("winflexbison/2.5.24")
        else:
            self.build_requires("flex/2.6.4")
            self.build_requires("bison/3.7.6")

    def requirements(self):
        self.requires("glib/2.73.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_meson(self):
        meson = Meson(self)
        defs = dict()
        defs["build_introspection_data"] = self.options["glib"].shared
        defs["datadir"] = os.path.join(self.package_folder, "res")

        meson.configure(
            source_folder=self.source_folder,
            args=["--wrap-mode=nofallback"],
            build_folder=self._build_subfolder,
            defs=defs,
        )
        return meson

    def build(self):
        replace_in_file(
            self, os.path.join(self.source_folder, "meson.build"), "subdir('tests')", "#subdir('tests')"
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "meson.build"),
            "if meson.version().version_compare('>=0.54.0')",
            "if false",
        )

        with environment_append(
            self,
            VisualStudioBuildEnvironment(self).vars
            if is_msvc(self)
            else {"PKG_CONFIG_PATH": self.build_folder},
        ):
            meson = self._configure_meson()
            meson.build()

    def package(self):
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        with environment_append(self, VisualStudioBuildEnvironment(self).vars) if is_msvc(self) else no_op(
            self
        ):
            meson = self._configure_meson()
            meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        for pdb_file in glob.glob(os.path.join(self.package_folder, "bin", "*.pdb")):
            os.unlink(pdb_file)

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "gobject-introspection-1.0"
        self.cpp_info.libs = ["girepository-1.0"]
        self.cpp_info.includedirs.append(os.path.join("include", "gobject-introspection-1.0"))

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var with: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        exe_ext = ".exe" if self.settings.os == "Windows" else ""

        pkgconfig_variables = {
            "datadir": "${prefix}/res",
            "bindir": "${prefix}/bin",
            "g_ir_scanner": "${bindir}/g-ir-scanner",
            "g_ir_compiler": "${bindir}/g-ir-compiler%s" % exe_ext,
            "g_ir_generate": "${bindir}/g-ir-generate%s" % exe_ext,
            "gidatadir": "${datadir}/gobject-introspection-1.0",
            "girdir": "${datadir}/gir-1.0",
            "typelibdir": "${libdir}/girepository-1.0",
        }
        self.cpp_info.set_property(
            "pkg_config_custom_content",
            "\n".join("%s=%s" % (key, value) for key, value in pkgconfig_variables.items()),
        )
