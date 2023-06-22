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


class RangesnextConan(ConanFile):
    name = "rangesnext"
    description = "ranges features for C++23 ported to C++20"
    topics = ("ranges", "backport", "backport-cpp")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/cor3ntin/rangesnext"
    license = "BSL-1.0"
    settings = "compiler"
    no_copy_source = True

    _compilers_minimum_version = {
        "gcc": "10",
        "Visual Studio": "19",
        "clang": "13",
    }
    _source_subfolder = "source_subfolder"

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "20")

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version or Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                "rangesnext requires C++20, which your compiler does not fully support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        include_folder = os.path.join(self.source_folder, "include")
        copy(
            self,
            pattern="LICENSE.md",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "include"), src=include_folder)
