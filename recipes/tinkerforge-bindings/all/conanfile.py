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

required_conan_version = ">=1.43.0"


class TinkerforgeBindingsConan(ConanFile):
    name = "tinkerforge-bindings"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.tinkerforge.com/"
    license = "CC0 1.0 Universal"
    description = "API bindings to control Tinkerforge's Bricks and Bricklets"
    topics = ("iot", "maker", "bindings")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def validate(self):
        if (
            self.settings.compiler == "Visual Studio"
            and self.options.shared
            and "MT" in self.settings.compiler.runtime
        ):
            raise ConanInvalidConfiguration("Static runtime + shared is failing to link")

    def source(self):
        get(
            self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=False
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "license.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "tinkerforge::bindings")

        self.cpp_info.names["cmake_find_package"] = "tinkerforge"
        self.cpp_info.names["cmake_find_package_multi"] = "tinkerforge"
        self.cpp_info.filenames["cmake_find_package"] = "tinkerforge-bindings"
        self.cpp_info.filenames["cmake_find_package_multi"] = "tinkerforge-bindings"
        self.cpp_info.components["_bindings"].names["cmake_find_package"] = "bindings"
        self.cpp_info.components["_bindings"].names["cmake_find_package_multi"] = "bindings"
        self.cpp_info.components["_bindings"].libs = ["tinkerforge_bindings"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_bindings"].system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["_bindings"].system_libs = ["advapi32", "ws2_32"]
