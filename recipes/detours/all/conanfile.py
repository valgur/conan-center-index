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

required_conan_version = ">=1.45.0"


class DetoursConan(ConanFile):
    name = "detours"
    homepage = "https://github.com/antlr/antlr4/tree/master/runtime/Cpp"
    description = "Detours is a software package for monitoring and instrumenting API calls on Windows"
    topics = ("monitoror", "instrumenting", "hook", "injection")
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Only os=Windows is supported")
        # if not is_msvc(self):
        #     raise ConanInvalidConfiguration("Only the MSVC compiler is supported")
        if is_msvc(self) and not is_msvc_static_runtime(self):
            # Debug and/or dynamic runtime is undesired for a hooking library
            raise ConanInvalidConfiguration("Only static runtime is supported (MT)")
        if self.settings.build_type != "Release":
            raise ConanInvalidConfiguration("Detours only supports the Release build type")
        try:
            self.output.info(f"target process is {self._target_processor}")
        except KeyError:
            raise ConanInvalidConfiguration("Unsupported architecture")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    @property
    def _target_processor(self):
        return {
            "x86": "X86",
            "x86_64": "X64",
            "armv7": "ARM",
            "armv8": "ARM64",
        }[str(self.settings.arch)]

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        if is_msvc(self):
            replace_in_file(
                self,
                os.path.join(self.source_folder, "src", "Makefile"),
                "/MT ",
                f"/{self.settings.compiler.runtime} ",
            )

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            with vcvars(self):
                with chdir(self, os.path.join(self.source_folder, "src")):
                    self.run(f"nmake DETOURS_TARGET_PROCESSOR={self._target_processor}")
        else:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            copy(
                self,
                "detours.lib",
                src=os.path.join(self.source_folder, f"lib.{self._target_processor}"),
                dst=os.path.join(self.package_folder, "lib"),
            )
            copy(
                self,
                "*.h",
                src=os.path.join(self.source_folder, "include"),
                dst=os.path.join(self.package_folder, "include"),
            )
        else:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libs = ["detours"]
        if self.settings.compiler == "gcc":
            self.cpp_info.system_libs = [stdcpp_library(self)]
            self.cpp_info.link_flags = ["-static-libgcc", "-static-libstdc++"]
