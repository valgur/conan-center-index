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

required_conan_version = ">=1.33.0"


class LibdivideConan(ConanFile):
    name = "libdivide"
    description = "Header-only C/C++ library for optimizing integer division."
    topics = ("libdivide", "division", "integer")
    license = ["Zlib", "BSL-1.0"]
    homepage = "http://libdivide.com/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "arch", "compiler"
    no_copy_source = True
    options = {
        "simd_intrinsics": [False, "sse2", "avx2", "avx512"],
        "sse2": [True, False],
        "avx2": [True, False],
        "avx512": [True, False],
        "neon": [True, False],
    }
    default_options = {
        "simd_intrinsics": False,
        "sse2": False,
        "avx2": False,
        "avx512": False,
        "neon": False,
    }

    def config_options(self):
        if Version(self.version) < "4.0.0":
            self.options.rm_safe("sse2")
            self.options.rm_safe("avx2")
            self.options.rm_safe("avx512")
            self.options.rm_safe("neon")
            if self.settings.arch not in ["x86", "x86_64"]:
                self.options.rm_safe("simd_intrinsics")
        else:
            self.options.rm_safe("simd_intrinsics")
            if self.settings.arch not in ["x86", "x86_64"]:
                self.options.rm_safe("sse2")
                self.options.rm_safe("avx2")
                self.options.rm_safe("avx512")
            if not str(self.settings.arch).startswith("arm"):
                self.options.rm_safe("neon")

    def configure(self):
        if Version(self.version) < "4.0.0" and self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "libdivide.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(
            self,
            "constant_fast_div.h",
            dst=os.path.join(self.package_folder, "include"),
            src=self.source_folder,
        )
        copy(self, "s16_ldparams.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(self, "u16_ldparams.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)

    def package_info(self):
        simd = self.options.get_safe("simd_intrinsics", False)
        if bool(simd):
            self.cpp_info.defines = [
                {
                    "sse2": "LIBDIVIDE_SSE2",
                    "avx2": "LIBDIVIDE_AVX2",
                    "avx512": "LIBDIVIDE_AVX512",
                }[str(simd)]
            ]
        if self.options.get_safe("sse2", False):
            self.cpp_info.defines.append("LIBDIVIDE_SSE2")
        if self.options.get_safe("avx2", False):
            self.cpp_info.defines.append("LIBDIVIDE_AVX2")
        if self.options.get_safe("avx512", False):
            self.cpp_info.defines.append("LIBDIVIDE_AVX512")
        if self.options.get_safe("neon", False):
            self.cpp_info.defines.append("LIBDIVIDE_NEON")
