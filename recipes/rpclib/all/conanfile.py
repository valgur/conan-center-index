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
from conan.tools.microsoft import msvc_runtime_flag
import os

required_conan_version = ">=1.43.0"


class rpclibConan(ConanFile):
    name = "rpclib"
    description = "A modern C++ msgpack-RPC server and client library."
    license = "MIT"
    topics = ("rpc", "ipc", "rpc-server")
    homepage = "https://github.com/rpclib/rpclib/"
    url = "https://github.com/conan-io/conan-center-index"
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

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if "MT" in str(msvc_runtime_flag(self)):
            tc.variables["RPCLIB_MSVC_STATIC_RUNTIME"] = True
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "rpclib")
        self.cpp_info.set_property("cmake_target_name", "rpclib::rpc")
        self.cpp_info.set_property("pkg_config_name", "rpclib")

        # Fix for installing dll to lib folder
        # - Default CMAKE installs the dll to the lib folder
        #   causing the test_package to fail
        if self.settings.os in ["Windows"]:
            if self.options.shared:
                self.cpp_info.components["_rpc"].bindirs.append(os.path.join(self.package_folder, "lib"))

        # TODO: Remove after Conan 2.0
        self.cpp_info.components["_rpc"].names["cmake_find_package"] = "rpc"
        self.cpp_info.components["_rpc"].names["cmake_find_package_multi"] = "rpc"
        self.cpp_info.components["_rpc"].libs = ["rpc"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_rpc"].system_libs = ["pthread"]
        self.cpp_info.names["pkg_config"] = "librpc"
