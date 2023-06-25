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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class AzureStorageCppConan(ConanFile):
    name = "azure-storage-cpp"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Azure/azure-storage-cpp"
    description = "Microsoft Azure Storage Client Library for C++"
    topics = ("azure", "cpp", "cross-platform", "microsoft", "cloud")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        copy(self, "cmake-wrapper.cmd", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    @property
    def _minimum_cpp_standard(self):
        return 11

    @property
    def _minimum_compiler_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "14",
            "clang": "3.4",
            "apple-clang": "5.1",
        }

    def requirements(self):
        self.requires("cpprestsdk/2.10.18")
        if self.settings.os != "Windows":
            self.requires("boost/1.76.0")
            self.requires("libxml2/2.9.10")
            self.requires("libuuid/1.0.3")
        if self.settings.os == "Macos":
            self.requires("libgettext/0.20.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compiler_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    "{} requires C++{} support. The current compiler {} {} does not support it.".format(
                        self.name,
                        self._minimum_cpp_standard,
                        self.settings.compiler,
                        self.settings.compiler.version,
                    )
                )

        # FIXME: Visual Studio 2015 & 2017 are supported but CI of CCI lacks several Win SDK components
        # https://github.com/conan-io/conan-center-index/issues/4195
        if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version) < "16":
            raise ConanInvalidConfiguration("Visual Studio < 2019 not yet supported in this recipe")
        if (
            self.settings.compiler == "Visual Studio"
            and self.options.shared
            and "MT" in self.settings.compiler.runtime
        ):
            raise ConanInvalidConfiguration(
                "Visual Studio build for shared library with MT runtime is not supported"
            )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_FRAMEWORK"] = "LAST"
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_SAMPLES"] = False
        if not self.settings.compiler.cppstd:
            tc.variables["CMAKE_CXX_STANDARD"] = self._minimum_cpp_standard
        if self.settings.os == "Macos":
            tc.variables["GETTEXT_LIB_DIR"] = self.dependencies["libgettext"].cpp_info.libdirs[0]
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "rpcrt4", "xmllite", "bcrypt"]
            if not self.options.shared:
                self.cpp_info.defines = ["_NO_WASTORAGE_API"]
