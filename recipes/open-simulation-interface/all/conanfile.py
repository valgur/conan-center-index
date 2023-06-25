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
import shutil

required_conan_version = ">=1.33.0"


class OpenSimulationInterfaceConan(ConanFile):
    name = "open-simulation-interface"
    homepage = "https://github.com/OpenSimulationInterface/open-simulation-interface"
    description = (
        "Generic interface environmental perception of automated driving functions in virtual scenarios"
    )
    topics = ("asam", "adas", "open-simulation", "automated-driving", "openx")
    url = "https://github.com/conan-io/conan-center-index"
    license = "MPL-2.0"
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
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)
        if self.options.shared:
            if self.settings.os == "Windows":
                raise ConanInvalidConfiguration(
                    "Shared Libraries are not supported on windows because of the missing symbol export in the library."
                )

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("protobuf/3.17.1")

    def build_requirements(self):
        self.build_requires("protobuf/3.17.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        try:
            if self.settings.os == "Windows":
                shutil.rmtree(os.path.join(self.package_folder, "CMake"))
            else:
                shutil.rmtree(os.path.join(self.package_folder, "lib", "cmake"))
        except:
            pass

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "open_simulation_interface"
        self.cpp_info.names["cmake_find_package_multi"] = "open_simulation_interface"
        self.cpp_info.components["libopen_simulation_interface"].names[
            "cmake_find_package"
        ] = "open_simulation_interface"
        self.cpp_info.components["libopen_simulation_interface"].names[
            "cmake_find_package_multi"
        ] = "open_simulation_interface"
        self.cpp_info.components["libopen_simulation_interface"].libs = ["open_simulation_interface"]
        self.cpp_info.components["libopen_simulation_interface"].requires = ["protobuf::libprotobuf"]
