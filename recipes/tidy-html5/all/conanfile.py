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

required_conan_version = ">=1.33.0"


class TidyHtml5Conan(ConanFile):
    name = "tidy-html5"
    license = "W3C"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.html-tidy.org"
    description = "The granddaddy of HTML tools, with support for modern standards"
    topics = ("html", "parser", "xml", "tools")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "support_localizations": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "support_localizations": True,
    }

    exports_sources = ["CMakeLists.txt", "patches/**"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TAB2SPACE"] = False
        tc.variables["BUILD_SAMPLE_CODE"] = False
        tc.variables["TIDY_COMPAT_HEADERS"] = False
        tc.variables["SUPPORT_CONSOLE_APP"] = False
        tc.variables["SUPPORT_LOCALIZATIONS"] = self.options.support_localizations
        tc.variables["ENABLE_DEBUG_LOG"] = False
        tc.variables["ENABLE_ALLOC_DEBUG"] = False
        tc.variables["ENABLE_MEMORY_DEBUG"] = False
        tc.variables["BUILD_SHARED_LIB"] = self.options.shared
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst="licenses", src=self.source_folder)
        copy(self, "LICENSE.md", dst="licenses", src=os.path.join(self.source_folder, "README"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"), recursive=True)
        if self.options.shared:
            to_remove = "*tidy_static*" if self.settings.os == "Windows" else "*.a"
            rm(self, to_remove, os.path.join(self.package_folder, "lib"), recursive=True)

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "tidy"
        suffix = "_static" if self.settings.os == "Windows" and not self.options.shared else ""
        suffix += (
            "d" if self.settings.compiler == "Visual Studio" and self.settings.build_type == "Debug" else ""
        )
        self.cpp_info.libs = ["tidy" + suffix]
        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.defines.append("TIDY_STATIC")
