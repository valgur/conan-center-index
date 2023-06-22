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


class TypeSafe(ConanFile):
    name = "type_safe"
    description = "Zero overhead utilities for preventing bugs at compile time"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://foonathan.net/type_safe"
    license = "MIT"
    topics = ("c++", "strong typing", "vocabulary-types")

    settings = "compiler"

    no_copy_source = True
    _source_subfolder = "source_subfolder"

    def requirements(self):
        self.requires("debug_assert/1.3.3")

    @property
    def _repo_folder(self):
        return self.source_folder

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def configure(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")

    def package(self):
        copy(self, "*LICENSE", dst="licenses", keep_path=False)
        copy(self, "*", src=os.path.join(self._repo_folder, "include"), dst="include/")

    def package_id(self):
        self.info.header_only()
