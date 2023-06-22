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
    exports_sources = ["CMakeLists.txt", "patches/**"]
    generators = "cmake"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def _patch_sources(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "flatbuffers-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def generate(self):
        cmake = CMake(self)
        cmake.definitions["FLATBUFFERS_BUILD_TESTS"] = False
        cmake.definitions["FLATBUFFERS_BUILD_SHAREDLIB"] = False
        cmake.definitions["FLATBUFFERS_BUILD_FLATLIB"] = True
        cmake.definitions["FLATBUFFERS_BUILD_FLATC"] = True
        cmake.definitions["FLATBUFFERS_BUILD_FLATHASH"] = True
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE.txt", dst="licenses", src=self._source_subfolder)
        extension = ".exe" if self.settings.os == "Windows" else ""
        bin_dir = os.path.join(self._build_subfolder, "bin")
        self.copy(pattern="flatc" + extension, dst="bin", src=bin_dir)
        self.copy(pattern="flathash" + extension, dst="bin", src=bin_dir)
        self.copy(
            pattern="BuildFlatBuffers.cmake",
            dst="bin/cmake",
            src=os.path.join(self._source_subfolder, "CMake"),
        )

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: %s" % bin_path)
        self.env_info.PATH.append(bin_path)
        self.cpp_info.builddirs.append("bin/cmake")
        self.cpp_info.build_modules.append("bin/cmake/BuildFlatBuffers.cmake")
