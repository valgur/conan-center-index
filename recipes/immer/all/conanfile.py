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

required_conan_version = ">=1.33.0"


class ImmerConan(ConanFile):
    name = "immer"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/arximboldi/immer"
    description = "Postmodern immutable and persistent data structures for C++---value semantics at scale"
    topics = (
        "header",
        "header-only",
        "persistent",
        "modern",
        "immutable",
        "data structures",
        "functional",
        "value semantics",
        "postmodern",
        "rrb-tree",
    )
    no_copy_source = True
    settings = "compiler"

    @property
    def _minimum_cpp_standard(self):
        return 14

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        include_folder = self.source_folder
        copy(self, pattern="*.hpp", dst=os.path.join(self.package_folder, "include"), src=include_folder)
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=include_folder)

    def package_id(self):
        self.info.header_only()

    @property
    def _minimum_compilers_version(self):
        # Reference: https://en.cppreference.com/w/cpp/compiler_support/14
        return {
            "apple-clang": "5.1",
            "clang": "3.4",
            "gcc": "6",
            "intel": "17",
            "sun-cc": "5.15",
            "Visual Studio": "15",
        }

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise errors.ConanInvalidConfiguration(
                    "{} requires C++{} support. The current compiler {} {} does not support it.".format(
                        self.name,
                        self._minimum_cpp_standard,
                        self.settings.compiler,
                        self.settings.compiler.version,
                    )
                )
