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

required_conan_version = ">=1.43.0"


class DaggyConan(ConanFile):
    name = "daggy"
    license = "MIT"
    homepage = "https://daggy.dev"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Data Aggregation Utility and C/C++ developer library for data streams catching"
    topics = (
        "streaming",
        "qt",
        "monitoring",
        "process",
        "stream-processing",
        "extensible",
        "serverless-framework",
        "aggregation",
        "ssh2",
        "crossplatform",
        "ssh-client",
    )

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "with_ssh2": [True, False],
        "with_yaml": [True, False],
        "with_console": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "with_ssh2": True,
        "with_yaml": True,
        "with_console": False,
        "shared": False,
        "fPIC": True,
    }

    @property
    def _minimum_cpp_standard(self):
        return 17

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build_requirements(self):
        self.build_requires("cmake/3.21.3")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        self.options["qt"].shared = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16",
            "gcc": "8",
            "clang": "8",
            "apple-clang": "10",
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
                raise ConanInvalidConfiguration(
                    "{} requires C++{} support. The current compiler {} {} does not support it.".format(
                        self.name,
                        self._minimum_cpp_standard,
                        self.settings.compiler,
                        self.settings.compiler.version,
                    )
                )

        if not self.options["qt"].shared:
            raise ConanInvalidConfiguration("Shared Qt lib is required.")

    def requirements(self):
        self.requires("qt/6.2.2")
        self.requires("kainjow-mustache/4.1")

        if self.options.with_yaml:
            self.requires("yaml-cpp/0.7.0")

        if self.options.with_ssh2:
            self.requires("libssh2/1.10.0")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_CXX_STANDARD"] = 17
        tc.variables["CMAKE_CXX_STANDARD_REQUIRED"] = True
        tc.variables["SSH2_SUPPORT"] = self.options.with_ssh2
        tc.variables["YAML_SUPPORT"] = self.options.with_yaml
        tc.variables["CONSOLE"] = self.options.with_console
        tc.variables["PACKAGE_DEPS"] = False
        tc.variables["VERSION"] = self.version
        tc.variables["CONAN_BUILD"] = True
        tc.variables["BUILD_TESTING"] = False

        if self.options.shared:
            tc.variables["CMAKE_C_VISIBILITY_PRESET"] = "hidden"
            tc.variables["CMAKE_CXX_VISIBILITY_PRESET"] = "hidden"
            tc.variables["CMAKE_VISIBILITY_INLINES_HIDDEN"] = 1
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False,
        )

    def package_info(self):
        self.cpp_info.libs = ["DaggyCore"]
