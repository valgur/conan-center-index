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

required_conan_version = ">=1.33.0"


class CppProjectFrameworkConan(ConanFile):
    name = "cpp_project_framework"
    license = "AGPL-3.0"
    homepage = "https://github.com/sheepgrass/cpp_project_framework"
    url = "https://github.com/conan-io/conan-center-index"  # Package recipe repository url here, for issues about the package
    description = "C++ Project Framework is a framework for creating C++ project."
    topics = ("cpp", "project", "framework")
    settings = "os", "compiler", "build_type", "arch"

    def package_id(self):
        self.info.header_only()

    @property
    def _minimum_cpp_standard(self):
        return 14

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16",
            "gcc": "7",
            "clang": "6",
            "apple-clang": "10",
        }

    def validate(self):
        if self.settings.os not in ("Linux", "Windows"):
            raise ConanInvalidConfiguration(f"{self.name} is just supported for Linux and Windows")

        compiler = self.settings.compiler

        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)

        if compiler in ("gcc", "clang"):
            if compiler.get_safe("libcxx") != "libstdc++":
                raise ConanInvalidConfiguration(f"only supported {compiler} with libstdc++")

        min_version = self._minimum_compilers_version.get(str(compiler))
        if not min_version:
            self.output.warn(f"{self.name} recipe lacks information about the {compiler} compiler support.")
        else:
            if Version(compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires C++{self._minimum_cpp_standard} support. The current compiler {compiler} {compiler.version} does not support it."
                )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*.h",
            dst=os.path.join("include", self.name),
            src=os.path.join(self.source_folder, self.name),
        )
