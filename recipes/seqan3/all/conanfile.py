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

required_conan_version = ">=1.43.0"


class Seqan3Conan(ConanFile):
    name = "seqan3"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/seqan/seqan3"
    description = "SeqAn3 is the new version of the popular SeqAn template library for the analysis of biological sequences."
    topics = ("cpp20", "algorithms", "data structures", "biological sequences")
    license = "BSD-3-Clause"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "10",
        }

    def package_id(self):
        self.info.header_only()

    def validate(self):
        if self.settings.compiler != "gcc":
            raise ConanInvalidConfiguration("SeqAn3 only supports GCC.")

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 20)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version:
            if Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "SeqAn3 requires C++20, which your compiler does not fully support."
                )
        else:
            self.output.warn("SeqAn3 requires C++20. Your compiler is unknown. Assuming it supports C++20.")

        if self.settings.compiler == "gcc" and self.settings.compiler.libcxx != "libstdc++11":
            self.output.warn(
                "SeqAn3 does not actively support libstdc++, consider using libstdc++11 instead."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            "*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
            keep_path=True,
        )
        for submodule in ["range-v3", "cereal", "sdsl-lite"]:
            copy(
                self,
                "*.hpp",
                dst=os.path.join(self.package_folder, "include"),
                src=os.path.join(self.source_folder, "submodules", submodule, "include"),
                keep_path=True,
            )
        copy(self, "LICENSE.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "seqan3")
        self.cpp_info.set_property("cmake_target_name", "seqan3::seqan3")
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
