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

required_conan_version = ">=1.36.0"


class HiredisConan(ConanFile):
    name = "hiredis"
    description = "Hiredis is a minimalistic C client library for the Redis database."
    license = "BSD-3-Clause"
    topics = ("redis", "client", "database")
    homepage = "https://github.com/redis/hiredis"
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

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("hiredis {} is not supported on Windows.".format(self.version))

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Do not force PIC if static
        if not self.options.shared:
            makefile = os.path.join(self.source_folder, "Makefile")
            replace_in_file(self, makefile, "-fPIC ", "")

    def build(self):
        self._patch_sources()
        with chdir(self.source_folder):
            autoTools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            autoTools.make()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        with chdir(self.source_folder):
            autoTools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            autoTools.install(
                vars={
                    "DESTDIR": unix_path(self.package_folder),
                    "PREFIX": "",
                }
            )
        remove_files_by_mask(
            self, os.path.join(self.package_folder, "lib"), "*.a" if self.options.shared else "*.[so|dylib]*"
        )
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "hiredis")
        self.cpp_info.libs = ["hiredis"]
