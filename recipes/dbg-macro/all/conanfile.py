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


class DbgMacroConan(ConanFile):
    name = "dbg-macro"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/sharkdp/dbg-macro"
    license = "MIT"
    description = "A dbg(...) macro for C++"
    topics = ("debugging", "macro", "pretty-printing", "header-only")
    settings = ("compiler",)
    no_copy_source = True

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def configure(self):
        minimal_cpp_standard = "11"
        if self.settings.get_safe("compiler.cppstd"):
            check_min_cppstd(self, minimal_cpp_standard)

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration(
                "dbg-mcro can't be used by {0} {1}".format(
                    self.settings.compiler, self.settings.compiler.version
                )
            )

    def package(self):
        copy(self, "dbg.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_id(self):
        self.info.header_only()
