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

required_conan_version = ">=1.33.0"


class PlatformConvertersConan(ConanFile):
    name = "platform.converters"
    license = "MIT"
    homepage = "https://github.com/linksplatform/Converters"
    url = "https://github.com/conan-io/conan-center-index"
    description = (
        "platform.converters is one of the libraries of the LinksPlatform modular framework, "
        "to provide conversions between different types"
    )
    topics = ("linksplatform", "cpp20", "converters", "any", "native")
    settings = "compiler", "arch"
    no_copy_source = True

    @property
    def _internal_cpp_subfolder(self):
        return os.path.join(self.source_folder, "cpp", "Platform.Converters")

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "10",
            "Visual Studio": "16",
            "clang": "14",
            "apple-clang": "14",
        }

    @property
    def _minimum_cpp_standard(self):
        return 20

    def validate(self):
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler))

        if not minimum_version:
            self.output.warn(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )

        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                "{}/{} requires c++{}, "
                "which is not supported by {} {}.".format(
                    self.name,
                    self.version,
                    self._minimum_cpp_standard,
                    self.settings.compiler,
                    self.settings.compiler.version,
                )
            )

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=self._internal_cpp_subfolder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
