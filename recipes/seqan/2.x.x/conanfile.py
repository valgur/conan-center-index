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


class SeqanConan(ConanFile):
    name = "seqan"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/seqan/seqan"
    description = """
SeqAn is an open source C++ library of efficient algorithms and data structures for the analysis of sequences
with the focus on biological data. Our library applies a unique generic design that guarantees high performance,
generality, extensibility, and integration with other libraries.
SeqAn is easy to use and simplifies the development of new software tools with a minimal loss of performance.
"""
    topics = (
        "conan",
        "cpp98",
        "cpp11",
        "cpp14",
        "cpp17",
        "algorithms",
        "data structures",
        "biological sequences",
    )
    license = "BSD-3-Clause"
    settings = "compiler"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "14",
            "clang": "3.4",
            "apple-clang": "3.4",
        }

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version:
            if Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "seqan requires C++14, which your compiler does not fully support."
                )
        else:
            self.output.warn("seqan requires C++14. Your compiler is unknown. Assuming it supports C++14.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "seqan-seqan-v" + self.version
        os.rename(extracted_dir, self.source_folder)

    def package(self):
        copy(
            self,
            "*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
            keep_path=True,
        )
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_id(self):
        self.info.header_only()
