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


class CrowConan(ConanFile):
    name = "crow"
    homepage = "https://github.com/ipkn/crow"
    description = "Crow is C++ microframework for web. (inspired by Python Flask)"
    topics = ("web", "microframework", "header-only")
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "compiler", "arch", "build_type"
    license = "BSD-3-Clause"

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        self.requires("boost/1.69.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "crow-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def build(self):
        if Version(self.deps_cpp_info["boost"].version) >= "1.70.0":
            raise ConanInvalidConfiguration("Crow requires Boost <1.70.0")

        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(source_folder=self.source_folder)
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(self, "*.h", dst=os.path.join("include", "crow"), src="amalgamate")

    def package_id(self):
        self.info.header_only()

    def package_info(self):
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["pthread"]
