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


class PlatformDelegatesConan(ConanFile):
    name = "platform.delegates"
    license = "MIT"
    homepage = "https://github.com/linksplatform/Delegates"
    url = "https://github.com/conan-io/conan-center-index"
    description = """platform.delegates is one of the libraries of the LinksPlatform modular framework, which uses
    innovations from the C++17 standard, for easier use delegates/events in csharp style."""
    topics = ("linksplatform", "cpp17", "delegates", "events", "header-only")
    settings = "compiler"
    no_copy_source = True

    @property
    def _internal_cpp_subfolder(self):
        return os.path.join(self.source_folder, "cpp", "Platform.Delegates")

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "8",
            "Visual Studio": "16",
            "clang": "14",
            "apple-clang": "14",
        }

    @property
    def _minimum_cpp_standard(self):
        return 17

    def validate(self):
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler))

        if not minimum_version:
            self.output.warn(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )

        if Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                "platform.delegates/{} "
                "requires C++{} with {}, "
                "which is not supported "
                "by {} {}.".format(
                    self.version,
                    self._minimum_cpp_standard,
                    self.settings.compiler,
                    self.settings.compiler,
                    self.settings.compiler.version,
                )
            )

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "*.h", dst="include", src=self._internal_cpp_subfolder)
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)

    def package_id(self):
        self.info.header_only()
