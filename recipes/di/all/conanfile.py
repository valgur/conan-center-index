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


class DiConan(ConanFile):
    name = "di"
    license = "BSL-1.0"
    homepage = "https://github.com/boost-ext/di"
    url = "https://github.com/conan-io/conan-center-index"
    description = "DI: C++14 Dependency Injection Library."
    topics = ("dependency-injection", "metaprogramming", "design-patterns")
    settings = "compiler"
    options = {"with_extensions": [True, False], "diagnostics_level": [0, 1, 2]}
    default_options = {"with_extensions": False, "diagnostics_level": 1}
    no_copy_source = True

    def export_sources(self):
        copy(self, "BSL-1.0.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def configure(self):
        minimal_cpp_standard = "14"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)
        minimal_version = {
            "gcc": "5",
            "clang": "3.4",
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

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "di-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def package(self):
        copy(self, "BSL-1.0.txt", src="", dst="licenses")
        if self.options.with_extensions:
            copy(
                self,
                "*.hpp",
                src=os.path.join(self.source_folder, "extension", "include", "boost", "di", "extension"),
                dst=os.path.join("include", "boost", "di", "extension"),
                keep_path=True,
            )
        copy(
            self,
            "di.hpp",
            src=os.path.join(self.source_folder, "include", "boost"),
            dst=os.path.join("include", "boost"),
        )

    def package_id(self):
        self.info.requires.clear()
        self.info.settings.clear()
        del self.info.options.diagnostics_level

    def package_info(self):
        self.cpp_info.defines.append(
            "BOOST_DI_CFG_DIAGNOSTICS_LEVEL={}".format(self.options.diagnostics_level)
        )
