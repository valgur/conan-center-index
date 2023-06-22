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
import glob


class ResourcePool(ConanFile):
    name = "resource_pool"
    description = (
        "C++ header only library purposed to create pool of some " "resources like keepalive connections"
    )
    topics = ("resource pool", "asio", "elsid", "c++17", "cpp17")
    package_type = "header-library"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://github.com/elsid/resource_pool"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "15",
            "clang": "5",
            "apple-clang": "10",
        }

    def requirements(self):
        self.requires("boost/1.75.0")

    def _validate_compiler_settings(self):
        compiler = self.settings.compiler
        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, "17")
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)

        if not minimum_version:
            self.output.warn(
                "resource_pool requires C++17. Your compiler is unknown. Assuming it supports C++17."
            )
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration("resource_pool requires a compiler that supports at least C++17")

    def validate(self):
        self._validate_compiler_settings()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = glob.glob(self.name + "-*/")[0]
        os.rename(extracted_dir, self.source_folder)

    def package(self):
        copy(
            self,
            pattern="*",
            dst=os.path.join("include", "yamail"),
            src=os.path.join(self.source_folder, "include", "yamail"),
        )
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        main_comp = self.cpp_info.components["_resource_pool"]
        main_comp.requires = ["boost::boost", "boost::system", "boost::thread"]
        main_comp.defines = ["BOOST_ASIO_USE_TS_EXECUTOR_AS_DEFAULT"]
        main_comp.names["cmake_find_package"] = "resource_pool"
        main_comp.names["cmake_find_package_multi"] = "resource_pool"

        if self.settings.os == "Windows":
            main_comp.system_libs.append("ws2_32")

        # Set up for compatibility with existing cmake configuration
        self.cpp_info.filenames["cmake_find_package"] = "resource_pool"
        self.cpp_info.filenames["cmake_find_package_multi"] = "resource_pool"
        self.cpp_info.names["cmake_find_package"] = "elsid"
        self.cpp_info.names["cmake_find_package_multi"] = "elsid"
