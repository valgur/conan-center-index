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
import os


class MathterConan(ConanFile):
    name = "mathter"
    license = "MIT"
    homepage = "https://github.com/petiaccja/Mathter"
    url = "https://github.com/conan-io/conan-center-index/"
    description = "Powerful 3D math and small-matrix linear algebra library for games and science."
    topics = ("game-dev", "linear-algebra", "vector-math", "matrix-library")
    no_copy_source = True
    settings = "compiler"

    @property
    def _compilers_minimum_version(self):
        return {"apple-clang": 10, "clang": 6, "gcc": 7, "Visual Studio": 16}

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "17")

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version:
            if Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "mathter requires C++17, which your compiler does not support."
                )
        else:
            self.output.warn("mathter requires C++17. Your compiler is unknown. Assuming it supports C++17.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("Mathter-" + self.version, self.source_folder)

    def package(self):
        copy(
            self,
            "*.hpp",
            dst=os.path.join("include", "Mathter"),
            src=os.path.join(self.source_folder, "Mathter"),
        )
        copy(
            self,
            "*.natvis",
            dst=os.path.join("include", "Mathter"),
            src=os.path.join(self.source_folder, "Mathter"),
        )
        copy(self, "LICENCE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_id(self):
        self.info.header_only()
