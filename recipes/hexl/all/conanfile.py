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
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc
from conan.tools.files import get, rmdir
from conan.tools.scm import Version
from conan.tools.build import cross_building
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

import os

required_conan_version = ">=1.43.0"


class HexlConan(ConanFile):
    name = "hexl"
    license = "Apache-2.0"
    homepage = "https://github.com/intel/hexl"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Intel Homomorphic Encryption (HE) Acceleration Library"
    topics = ("homomorphic", "encryption", "privacy")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "experimental": [True, False],
        "fpga_compatibility_dyadic_multiply": [True, False],
        "fpga_compatibility_keyswitch": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "experimental": False,
        "fpga_compatibility_dyadic_multiply": False,
        "fpga_compatibility_keyswitch": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build_requirements(self):
        self.build_requires("cmake/3.22.0")

    def requirements(self):
        self.requires("cpu_features/0.7.0")

        if self.settings.build_type == "Debug":
            self.requires("easyloggingpp/9.97.0")

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "15.7",
            "clang": "7",
            "apple-clang": "11",
        }

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 17)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version:
            if Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "{} requires C++17, which your compiler does not support.".format(self.name)
                )
        else:
            self.output.warn(
                "{} requires C++17. Your compiler is unknown. Assuming it supports C++17.".format(self.name)
            )

        if self.settings.arch not in ["x86", "x86_64"]:
            raise ConanInvalidConfiguration("Hexl only supports x86 architecture")

        if self.options.shared and is_msvc(self):
            raise ConanInvalidConfiguration("Hexl only supports static linking with msvc")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def generate(self):
        tc = CMakeToolchain(self)

        tc.variables["HEXL_BENCHMARK"] = False
        tc.variables["HEXL_TESTING"] = False
        tc.variables["HEXL_EXPERIMENTAL"] = self.options.experimental

        if self.options.fpga_compatibility_dyadic_multiply and self.options.fpga_compatibility_keyswitch:
            tc.variables["HEXL_FPGA_COMPATIBILITY"] = 3
        elif self.options.fpga_compatibility_dyadic_multiply:
            tc.variables["HEXL_FPGA_COMPATIBILITY"] = 1
        elif self.options.fpga_compatibility_keyswitch:
            tc.variables["HEXL_FPGA_COMPATIBILITY"] = 2
        else:
            tc.variables["HEXL_FPGA_COMPATIBILITY"] = 0

        tc.variables["HEXL_SHARED_LIB"] = self.options.shared
        tc.variables["HEXL_CROSS_COMPILED"] = cross_building(self)

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Hexl")
        # TODO: Remove in Conan 2.0
        self.cpp_info.names["cmake_find_package"] = "Hexl"
        self.cpp_info.names["cmake_find_package_multi"] = "Hexl"

        if self.settings.build_type == "Debug":
            if not is_msvc(self):
                self.cpp_info.components["Hexl"].libs = ["hexl_debug"]
            else:
                self.cpp_info.components["Hexl"].libs = ["hexl"]

            self.cpp_info.components["Hexl"].requires.append("easyloggingpp::easyloggingpp")
        else:
            self.cpp_info.components["Hexl"].libs = ["hexl"]

        self.cpp_info.components["Hexl"].names["cmake_find_package"] = "hexl"
        self.cpp_info.components["Hexl"].names["cmake_find_package_multi"] = "hexl"
        self.cpp_info.components["Hexl"].set_property("cmake_target_name", "Hexl::hexl")
        self.cpp_info.components["Hexl"].set_property("pkg_config_name", "hexl")
        self.cpp_info.components["Hexl"].requires.append("cpu_features::libcpu_features")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["Hexl"].system_libs = ["pthread", "m"]
