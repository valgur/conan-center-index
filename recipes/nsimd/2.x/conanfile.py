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


class NsimdConan(ConanFile):
    name = "nsimd"
    homepage = "https://github.com/agenium-scale/nsimd"
    description = "Agenium Scale vectorization library for CPUs and GPUs"
    topics = (
        "hpc",
        "neon",
        "cuda",
        "avx",
        "simd",
        "avx2",
        "sse2",
        "aarch64",
        "avx512",
        "sse42",
        "rocm",
        "sve",
        "neon128",
    )
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # This used only when building the library.
        # Most functionality is header only.
        "simd": [
            None,
            "cpu",
            "sse2",
            "sse42",
            "avx",
            "avx2",
            "avx512_knl",
            "avx512_skylake",
            "neon128",
            "aarch64",
            "sve",
            "sve128",
            "sve256",
            "sve512",
            "sve1024",
            "sve2048",
            "cuda",
            "rocm",
        ],
    }
    default_options = {"shared": False, "fPIC": True, "simd": None}

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # Most of the library is header only.
        # cpp files do not use STL.
        self.settings.rm_safe("compiler.libcxx")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.options.simd:
            tc.variables["simd"] = self.options.simd
        if self.settings.arch == "armv7hf":
            tc.variables["NSIMD_ARM32_IS_ARMEL"] = False
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        cmakefile_path = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(self, cmakefile_path, " SHARED ", " ")
        replace_in_file(self, cmakefile_path, "RUNTIME DESTINATION lib", "RUNTIME DESTINATION bin")
        replace_in_file(
            self, cmakefile_path, "set_property(TARGET ${o} PROPERTY POSITION_INDEPENDENT_CODE ON)", ""
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
