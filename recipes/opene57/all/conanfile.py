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


class Opene57Conan(ConanFile):
    name = "opene57"
    description = (
        "A C++ library for reading and writing E57 files, " "fork of the original libE57 (http://libe57.org)"
    )
    topics = ("e57", "libe57", "3d", "astm")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/openE57/openE57"
    license = ("MIT", "BSL-1.0")
    settings = "os", "compiler", "arch", "build_type"
    options = {
        "with_tools": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "with_tools": False,
        "shared": False,
        "fPIC": True,
    }

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "15",
            "gcc": "7",
            "clang": "6",
            "apple-clang": "10",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.with_tools:
            self.options["boost"].multithreading = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def validate(self):
        if self.options.shared:
            raise ConanInvalidConfiguration("OpenE57 cannot be built as shared library yet")

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        minimum_version = self._minimum_compilers_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warn("C++17 support required. Your compiler is unknown. Assuming it supports C++17.")
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration("C++17 support required, which your compiler does not support.")

    def requirements(self):
        if self.options.with_tools:
            self.requires("boost/1.78.0")

        if self.settings.os == "Linux" or is_apple_os(self.settings.os):
            self.requires("icu/70.1")

        self.requires("xerces-c/3.2.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PROJECT_VERSION"] = self.version
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_TOOLS"] = self.options.with_tools
        tc.variables["BUILD_TESTS"] = False
        if self.settings.compiler == "Visual Studio":
            tc.variables["BUILD_WITH_MT"] = "MT" in msvc_runtime_flag(self)
        else:
            tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        copy(
            self,
            pattern="LICENSE.libE57",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()
        os.remove(os.path.join(self.package_folder, "CHANGELOG.md"))
        rm(self, "*.dll", os.path.join(self.package_folder, "bin"), recursive=True)

    def package_info(self):
        if self.options.with_tools:
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info("Appending PATH env: {}".format(bin_path))
            self.env_info.PATH.append(bin_path)

        lib_suffix = "-d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"openE57{lib_suffix}", f"openE57las{lib_suffix}"]

        self.cpp_info.defines.append(f"E57_REFIMPL_REVISION_ID={self.name}-{self.version}")
        self.cpp_info.defines.append("XERCES_STATIC_LIBRARY")
