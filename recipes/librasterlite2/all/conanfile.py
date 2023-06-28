# Warnings:
#   Disallowed attribute 'generators = 'pkg_config''
#   Unexpected method '_configure_autotools'
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
import functools
import os

required_conan_version = ">=1.53.0"


class Librasterlite2Conan(ConanFile):
    name = "librasterlite2"
    description = (
        "librasterlite2 is an open source library that stores and retrieves huge raster coverages using a"
        " SpatiaLite DBMS."
    )
    license = ("MPL-1.1", "GPL-2.0-or-later", "LGPL-2.1-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gaia-gis.it/fossil/librasterlite2"
    topics = ("rasterlite", "raster", "spatialite")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openjpeg": [True, False],
        "with_webp": [True, False],
        "with_lzma": [True, False],
        "with_lz4": [True, False],
        "with_zstd": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openjpeg": True,
        "with_webp": True,
        "with_lzma": True,
        "with_lz4": True,
        "with_zstd": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cairo/1.17.4")
        self.requires("freetype/2.11.1")
        self.requires("giflib/5.2.1")
        self.requires("libcurl/7.80.0")
        self.requires("libgeotiff/1.7.1")
        self.requires("libjpeg/9d")
        self.requires("libpng/1.6.37")
        self.requires("libspatialite/5.0.1")
        self.requires("libtiff/4.3.0")
        self.requires("libxml2/2.9.13")
        self.requires("sqlite3/3.38.1")
        self.requires("zlib/1.2.12")
        if self.options.with_openjpeg:
            self.requires("openjpeg/2.4.0")
        if self.options.with_webp:
            self.requires("libwebp/1.2.2")
        if self.options.with_lzma:
            self.requires("xz_utils/5.2.5")
        if self.options.with_lz4:
            self.requires("lz4/1.9.3")
        if self.options.with_zstd:
            self.requires("zstd/1.5.2")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("Visual Studio not supported yet")

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")
        self.build_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Disable tests, tools and examples
        replace_in_file(
            self,
            os.path.join(self.source_folder, "Makefile.am"),
            "SUBDIRS = headers src test tools examples",
            "SUBDIRS = headers src",
        )
        # fix MinGW
        replace_in_file(
            self,
            os.path.join(self.source_folder, "configure.ac"),
            "AC_CHECK_LIB(z,",
            "AC_CHECK_LIB({},".format(self.dependencies["zlib"].cpp_info.libs[0]),
        )

    def generate(self):
        tc = AutotoolsToolchain(self)
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--disable-gcov",
            "--enable-openjpeg={}".format(yes_no(self.options.with_openjpeg)),
            "--enable-webp={}".format(yes_no(self.options.with_webp)),
            "--enable-lzma={}".format(yes_no(self.options.with_lzma)),
            "--enable-lz4={}".format(yes_no(self.options.with_lz4)),
            "--enable-zstd={}".format(yes_no(self.options.with_zstd)),
        ]
        tc.generate()

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            # relocatable shared libs on macOS
            replace_in_file(self, "configure", "-install_name \\$rpath/", "-install_name @rpath/")
            # avoid SIP issues on macOS when dependencies are shared
            if is_apple_os(self.settings.os):
                libdirs = []
                for dep in self.dependencies.values():
                    libdirs.extend(dep.cpp_info.aggregated_components().libdirs)
                libpaths = ":".join(libdirs)
                replace_in_file(
                    self,
                    "configure",
                    "#! /bin/sh\n",
                    "#! /bin/sh\nexport DYLD_LIBRARY_PATH={}:$DYLD_LIBRARY_PATH\n".format(libpaths),
                )
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "rasterlite2")
        self.cpp_info.libs = ["rasterlite2"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")

        # TODO: to remove in conan v2 once pkg_config generator removed
