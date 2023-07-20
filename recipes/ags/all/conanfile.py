# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import (
    collect_libs,
    copy,
    get,
)
from conan.tools.layout import basic_layout
from conan.tools.microsoft import (
    is_msvc,
    msvc_runtime_flag,
)

required_conan_version = ">=1.52.0"


class AGSConan(ConanFile):
    name = "ags"
    description = (
        "The AMD GPU Services (AGS) library provides software developers with the ability to query AMD GPU "
        "software and hardware state information that is not normally available through standard operating "
        "systems or graphics APIs."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/GPUOpen-LibrariesAndSDKs/AGS_SDK"
    topics = ("amd", "gpu", "header-only")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
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
        if not is_msvc(self):
            raise ConanInvalidConfiguration(
                "ags doesn't support compiler: {} on OS: {}.".format(self.settings.compiler, self.settings.os)
            )

        if is_msvc(self):
            if self.settings.compiler.version not in self._supported_msvc_versions:
                raise ConanInvalidConfiguration(
                    "ags doesn't support MSVC version: {}".format(self.settings.compiler.version)
                )
            if self.settings.arch not in self._supported_archs:
                raise ConanInvalidConfiguration("ags doesn't support arch: {}".format(self.settings.arch))

    def layout(self):
        basic_layout(self, src_folder="src")

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

        if is_msvc(self):
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
                    arch=win_arch, vs_version=vs_version, runtime=msvc_runtime_flag(self)
                )
                copy(
                    self,
                    static_lib,
                    dst=os.path.join(self.package_folder, "lib"),
                    src=os.path.join(ags_lib_path, "lib"),
                )

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
