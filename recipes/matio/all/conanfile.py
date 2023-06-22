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

required_conan_version = ">=1.33.0"


class MatioConan(ConanFile):
    name = "matio"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sourceforge.net/projects/matio/"
    description = "Matio is a C library for reading and writing binary MATLAB MAT files."
    topics = ("matlab", "mat-file", "file-format", "hdf5")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "extended_sparse": [True, False],
        "fPIC": [True, False],
        "mat73": [True, False],
        "with_hdf5": [True, False],
        "with_zlib": [True, False],
    }
    default_options = {
        "shared": False,
        "extended_sparse": True,
        "fPIC": True,
        "mat73": True,
        "with_hdf5": True,
        "with_zlib": True,
    }

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

    def requirements(self):
        if self.options.with_hdf5:
            self.requires("hdf5/1.12.1")
        if self.options.with_zlib:
            self.requires("zlib/1.2.12")

    def validate(self):
        if not self.options.with_hdf5 and self.options.mat73:
            raise ConanInvalidConfiguration("Support of version 7.3 MAT files requires HDF5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MATIO_EXTENDED_SPARSE"] = self.options.extended_sparse
        tc.variables["MATIO_PIC"] = self.options.get_safe("fPIC", True)
        tc.variables["MATIO_SHARED"] = self.options.shared
        tc.variables["MATIO_MAT73"] = self.options.mat73
        tc.variables["MATIO_WITH_HDF5"] = self.options.with_hdf5
        tc.variables["MATIO_WITH_ZLIB"] = self.options.with_zlib
        tc.variables["HDF5_USE_STATIC_LIBRARIES"] = self.options.with_hdf5 and not self.options["hdf5"].shared
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["libmatio"]
        else:
            self.cpp_info.libs = ["matio"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
