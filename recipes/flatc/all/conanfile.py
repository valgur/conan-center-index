"""Conan recipe package for Google FlatBuffers - Flatc
"""
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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class FlatcConan(ConanFile):
    name = "flatc"
    deprecated = "flatbuffers"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://google.github.io/flatbuffers/"
    topics = ("flatbuffers", "serialization", "rpc", "json-parser", "installer")
    description = "Memory Efficient Serialization Library"
    settings = "os", "arch"

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "flatbuffers-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        if is_msvc(self) and self.options.shared:
            tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["FLATBUFFERS_BUILD_TESTS"] = False
        tc.variables["FLATBUFFERS_BUILD_SHAREDLIB"] = False
        tc.variables["FLATBUFFERS_BUILD_FLATLIB"] = True
        tc.variables["FLATBUFFERS_BUILD_FLATC"] = True
        tc.variables["FLATBUFFERS_BUILD_FLATHASH"] = True

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        extension = ".exe" if self.settings.os == "Windows" else ""
        bin_dir = os.path.join(self.build_folder, "bin")
        copy(self, pattern="flatc" + extension, dst=os.path.join(self.package_folder, "bin"), src=bin_dir)
        copy(self, pattern="flathash" + extension, dst=os.path.join(self.package_folder, "bin"), src=bin_dir)
        copy(
            self,
            pattern="BuildFlatBuffers.cmake",
            dst=os.path.join(self.package_folder, "bin/cmake"),
            src=os.path.join(self.source_folder, "CMake"),
        )

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: %s" % bin_path)
        self.env_info.PATH.append(bin_path)
        self.cpp_info.builddirs.append("bin/cmake")
        self.cpp_info.build_modules.append("bin/cmake/BuildFlatBuffers.cmake")
