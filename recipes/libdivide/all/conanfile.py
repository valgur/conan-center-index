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
        if tools.Version(self.version) < "4.0.0":
            del self.options.sse2
            del self.options.avx2
            del self.options.avx512
            del self.options.neon
            if self.settings.arch not in ["x86", "x86_64"]:
                del self.options.simd_intrinsics
        else:
            del self.options.simd_intrinsics
            if self.settings.arch not in ["x86", "x86_64"]:
                del self.options.sse2
                del self.options.avx2
                del self.options.avx512
            if not str(self.settings.arch).startswith("arm"):
                del self.options.neon

    def configure(self):
        if tools.Version(self.version) < "4.0.0" and self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 11)

    def package_id(self):
        self.info.header_only()

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder
        )

    def package(self):
        self.copy("LICENSE.txt", dst="licenses", src=self._source_subfolder)
        self.copy("libdivide.h", dst="include", src=self._source_subfolder)
        self.copy("constant_fast_div.h", dst="include", src=self._source_subfolder)
        self.copy("s16_ldparams.h", dst="include", src=self._source_subfolder)
        self.copy("u16_ldparams.h", dst="include", src=self._source_subfolder)

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
