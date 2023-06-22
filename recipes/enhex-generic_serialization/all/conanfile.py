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


class EnhexGenericserializationConan(ConanFile):
    name = "enhex-generic_serialization"
    license = "MIT"
    description = "Lightweight and extensible generic serialization library"
    topics = "serialization"
    homepage = "https://github.com/Enhex/generic_serialization"
    url = "https://github.com/conan-io/conan-center-index"
    no_copy_source = True
    settings = "compiler"

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        minimal_version = {
            "Visual Studio": "15",
            "gcc": "7",
            "clang": "5.0",
            "apple-clang": "9.1",
        }
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)

        if compiler not in minimal_version:
            self.output.info("{} requires a compiler that supports at least C++17".format(self.name))
            return

        # Exclude compilers not supported
        if compiler_version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                "{} requires a compiler that supports at least C++17. {} {} is not".format(
                    self.name, compiler, Version(self.settings.compiler.version.value)
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            pattern="LICENSE.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )

    def package_id(self):
        self.info.header_only()
