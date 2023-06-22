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
import functools
import os
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.43.0"


class LibunifexConan(ConanFile):
    name = "libunifex"
    license = ("Apache-2.0", "LLVM-exception")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/facebookexperimental/libunifex"
    description = "A prototype implementation of the C++ sender/receiver async programming model"
    topics = ("async", "cpp")

    settings = "os", "arch", "compiler", "build_type"

    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "9",
            "Visual Studio": "16",
            "clang": "10",
            "apple-clang": "11",
        }

    @property
    def _minimum_standard(self):
        return "17"

    # FIXME: Add support for liburing
    # def requirements(self):
    # TODO: Make an option to opt-out of liburing for old kernel versions
    # if self.settings.os == "Linux":
    #    self.requires("liburing/2.1")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_standard)

        def lazy_lt_semver(v1, v2):
            lv1 = [int(v) for v in v1.split(".")]
            lv2 = [int(v) for v in v2.split(".")]
            min_length = min(len(lv1), len(lv2))
            return lv1[:min_length] < lv2[:min_length]

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warn(
                "{0} {1} requires C++{2}. Your compiler is unknown. Assuming it supports C++{2}.".format(
                    self.name, self.version, self._minimum_standard
                )
            )
        elif lazy_lt_semver(str(self.settings.compiler.version), minimum_version):
            raise ConanInvalidConfiguration(
                "{} {} requires C++{}, which your compiler does not support.".format(
                    self.name, self.version, self._minimum_standard
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = "OFF"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "unifex")
        self.cpp_info.set_property("cmake_target_name", "unifex::unifex")
        self.cpp_info.set_property("pkg_config_name", "unifex")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "unifex"
        self.cpp_info.filenames["cmake_find_package_multi"] = "unifex"
        self.cpp_info.names["cmake_find_package"] = "unifex"
        self.cpp_info.names["cmake_find_package_multi"] = "unifex"
        self.cpp_info.names["pkg_config"] = "unifex"
        self.cpp_info.components["unifex"].names["cmake_find_package"] = "unifex"
        self.cpp_info.components["unifex"].names["cmake_find_package_multi"] = "unifex"
        self.cpp_info.components["unifex"].set_property("cmake_target_name", "unifex::unifex")
        self.cpp_info.components["unifex"].libs = ["unifex"]

        if self.settings.os == "Linux":
            self.cpp_info.components["unifex"].system_libs = ["pthread"]
        #    self.cpp_info.components["unifex"].requires.append(
        #        "liburing::liburing")
