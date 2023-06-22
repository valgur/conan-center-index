# TODO: verify the Conan v2 migration

import glob
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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class libb2Conan(ConanFile):
    name = "libb2"
    license = ["CC0-1.0", "OpenSSL", "APSL-2.0"]
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/BLAKE2/BLAKE2"
    description = "libb2 is a library that implemets the BLAKE2 cryptographic hash function, which is faster than MD5, \
                    SHA-1, SHA-2, and SHA-3, yet is at least as secure as the latest standard SHA-3"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("blake2", "hash")
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "use_sse": [True, False],
        "use_neon": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "use_sse": False,
        "use_neon": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.use_neon and not "arm" in self.settings.arch:
            raise ConanInvalidConfiguration("Neon sources only supported on arm-based CPUs")
        if self.options.use_neon and self.options.use_sse:
            raise ConanInvalidConfiguration("Neon and SSE can not be used together.")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = glob.glob("BLAKE2-*")[0]
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_SSE"] = self.options.use_sse
        tc.variables["USE_NEON"] = self.options.use_neon
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst="licenses")
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs = ["include", os.path.join("include", "libb2")]
