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
import functools
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class FlatccConan(ConanFile):
    name = "flatcc"
    description = "C language binding for Flatbuffers, an efficient cross platform serialization library"
    license = "Apache-2.0"
    topics = ("flatbuffers", "serialization")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dvidelabs/flatcc"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "portable": [True, False],
        "gnu_posix_memalign": [True, False],
        "runtime_lib_only": [True, False],
        "verify_assert": [True, False],
        "verify_trace": [True, False],
        "reflection": [True, False],
        "native_optim": [True, False],
        "fast_double": [True, False],
        "ignore_const_condition": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "portable": False,
        "gnu_posix_memalign": True,
        "runtime_lib_only": False,
        "verify_assert": False,
        "verify_trace": False,
        "reflection": True,
        "native_optim": False,
        "fast_double": False,
        "ignore_const_condition": False,
    }
    generators = "cmake"
    exports_sources = ["CMakeLists.txt"]

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def validate(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and self.options.shared:
                # Building flatcc shared libs with Visual Studio is broken
                raise ConanInvalidConfiguration("Building flatcc libraries shared is not supported")
            if tools.Version(self.version) == "0.6.0" and self.settings.compiler == "gcc":
                raise ConanInvalidConfiguration("Building flatcc with MinGW is not supported")

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], destination=self._source_subfolder, strip_root=True
        )

    @functools.lru_cache(1)
    def generate(self):
        cmake = CMake(self)
        cmake.definitions["FLATCC_PORTABLE"] = self.options.portable
        cmake.definitions["FLATCC_GNU_POSIX_MEMALIGN"] = self.options.gnu_posix_memalign
        cmake.definitions["FLATCC_RTONLY"] = self.options.runtime_lib_only
        cmake.definitions["FLATCC_INSTALL"] = True
        cmake.definitions["FLATCC_COVERAGE"] = False
        cmake.definitions["FLATCC_DEBUG_VERIFY"] = self.options.verify_assert
        cmake.definitions["FLATCC_TRACE_VERIFY"] = self.options.verify_trace
        cmake.definitions["FLATCC_REFLECTION"] = self.options.reflection
        cmake.definitions["FLATCC_NATIVE_OPTIM"] = self.options.native_optim
        cmake.definitions["FLATCC_FAST_DOUBLE"] = self.options.fast_double
        cmake.definitions["FLATCC_IGNORE_CONST_COND"] = self.options.ignore_const_condition
        cmake.definitions["FLATCC_TEST"] = False
        cmake.definitions["FLATCC_ALLOW_WERROR"] = False
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        if self.settings.build_type == "Debug" and not tools.os_info.is_windows:
            debug_suffix = "_d" if self.settings.build_type == "Debug" else ""
            os.rename(
                os.path.join(self.package_folder, "bin", "flatcc%s" % debug_suffix),
                os.path.join(self.package_folder, "bin", "flatcc"),
            )
        # Copy license file
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: %s" % bin_path)
        self.env_info.PATH.append(bin_path)
        debug_suffix = "_d" if self.settings.build_type == "Debug" else ""
        if not self.options.runtime_lib_only:
            self.cpp_info.libs.append("flatcc%s" % debug_suffix)
        self.cpp_info.libs.append("flatccrt%s" % debug_suffix)
