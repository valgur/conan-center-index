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


class AGSConan(ConanFile):
    name = "ags"
    description = (
        "The AMD GPU Services (AGS) library provides software developers with the ability to query AMD GPU "
        "software and hardware state information that is not normally available through standard operating "
        "systems or graphics APIs."
    )
    homepage = "https://github.com/GPUOpen-LibrariesAndSDKs/AGS_SDK"
    topics = ("amd", "gpu")
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    license = "MIT"
    no_copy_source = True
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }

    @property
    def _supported_msvc_versions(self):
        return ["14", "15", "16"]

    @property
    def _supported_archs(self):
        return ["x86_64", "x86"]

    def configure(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("ags doesn't support OS: {}.".format(self.settings.os))
        if self.settings.compiler != "Visual Studio":
            raise ConanInvalidConfiguration(
                "ags doesn't support compiler: {} on OS: {}.".format(self.settings.compiler, self.settings.os)
            )

        if self.settings.compiler == "Visual Studio":
            if self.settings.compiler.version not in self._supported_msvc_versions:
                raise ConanInvalidConfiguration(
                    "ags doesn't support MSVC version: {}".format(self.settings.compiler.version)
                )
            if self.settings.arch not in self._supported_archs:
                raise ConanInvalidConfiguration("ags doesn't support arch: {}".format(self.settings.arch))

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _convert_msvc_version_to_vs_version(self, msvc_version):
        vs_versions = {
            "14": "2015",
            "15": "2017",
            "16": "2019",
        }
        return vs_versions.get(str(msvc_version), None)

    def _convert_arch_to_win_arch(self, msvc_version):
        vs_versions = {
            "x86_64": "x64",
            "x86": "x86",
        }
        return vs_versions.get(str(msvc_version), None)

    def package(self):
        ags_lib_path = os.path.join(self.source_folder, "ags_lib")
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=ags_lib_path)
        copy(
            self,
            "*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(ags_lib_path, "inc"),
        )

        if self.settings.compiler == "Visual Studio":
            win_arch = self._convert_arch_to_win_arch(self.settings.arch)
            if self.options.shared:
                shared_lib = "amd_ags_{arch}.dll".format(arch=win_arch)
                symbol_lib = "amd_ags_{arch}.lib".format(arch=win_arch)
                copy(
                    self,
                    shared_lib,
                    dst=os.path.join(self.package_folder, "bin"),
                    src=os.path.join(ags_lib_path, "lib"),
                )
                copy(
                    self,
                    symbol_lib,
                    dst=os.path.join(self.package_folder, "lib"),
                    src=os.path.join(ags_lib_path, "lib"),
                )
            else:
                vs_version = self._convert_msvc_version_to_vs_version(self.settings.compiler.version)
                static_lib = "amd_ags_{arch}_{vs_version}_{runtime}.lib".format(
                    arch=win_arch, vs_version=vs_version, runtime=self.settings.compiler.runtime
                )
                copy(
                    self,
                    static_lib,
                    dst=os.path.join(self.package_folder, "lib"),
                    src=os.path.join(ags_lib_path, "lib"),
                )

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
