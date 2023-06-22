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

required_conan_version = ">=1.43.0"


class SobjectizerConan(ConanFile):
    name = "sobjectizer"
    license = "BSD-3-Clause"
    homepage = "https://github.com/Stiffstream/sobjectizer"
    url = "https://github.com/conan-io/conan-center-index"
    description = (
        "A framework for simplification of development of sophisticated "
        "concurrent and event-driven applications in C++ "
        "by using Actor, Publish-Subscribe and CSP models."
    )
    topics = ("concurrency", "actor-framework", "actors", "agents", "actor-model", "publish-subscribe", "CSP")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        minimal_cpp_standard = "17"
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, minimal_cpp_standard)
        minimal_version = {
            "gcc": "7",
            "clang": "6",
            "apple-clang": "10",
            "Visual Studio": "15",
        }
        compiler = str(self.settings.compiler)
        if compiler not in minimal_version:
            self.output.warn(
                "%s recipe lacks information about the %s compiler standard version support"
                % (self.name, compiler)
            )
            self.output.warn(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )
            return

        version = Version(self.settings.compiler.version)
        if version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SOBJECTIZER_BUILD_SHARED"] = self.options.shared
        tc.variables["SOBJECTIZER_BUILD_STATIC"] = not self.options.shared
        tc.variables["SOBJECTIZER_INSTALL"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="dev/so_5")
        cmake.build()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            "license*",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            ignore_case=True,
            keep_path=False,
        )
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        cmake_target = "SharedLib" if self.options.shared else "StaticLib"
        self.cpp_info.set_property("cmake_file_name", "sobjectizer")
        self.cpp_info.set_property("cmake_target_name", "sobjectizer::{}".format(cmake_target))
        # TODO: back to global scope in conan v2 once cmake_find_package* generators removed
        self.cpp_info.components["_sobjectizer"].libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_sobjectizer"].system_libs = ["pthread", "m"]
        if not self.options.shared:
            self.cpp_info.components["_sobjectizer"].defines.append("SO_5_STATIC_LIB")

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.names["cmake_find_package"] = "sobjectizer"
        self.cpp_info.names["cmake_find_package_multi"] = "sobjectizer"
        self.cpp_info.components["_sobjectizer"].names["cmake_find_package"] = cmake_target
        self.cpp_info.components["_sobjectizer"].names["cmake_find_package_multi"] = cmake_target
        self.cpp_info.components["_sobjectizer"].set_property(
            "cmake_target_name", "sobjectizer::{}".format(cmake_target)
        )
