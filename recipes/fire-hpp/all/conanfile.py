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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class FireHppConan(ConanFile):
    name = "fire-hpp"
    homepage = "https://github.com/kongaskristjan/fire-hpp"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Fire for C++: Create fully functional CLIs using function signatures"
    topics = ("command-line", "argument", "parser")
    license = "BSL-1.0"
    no_copy_source = True
    settings = "os", "arch", "compiler", "build_type"

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FIRE_EXAMPLES"] = False
        tc.variables["FIRE_UNIT_TESTS"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENCE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_id(self):
        self.info.header_only()
