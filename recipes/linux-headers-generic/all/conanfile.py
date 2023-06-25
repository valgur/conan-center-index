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

required_conan_version = ">=1.33.0"


class LinuxHeadersGenericConan(ConanFile):
    name = "linux-headers-generic"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.kernel.org/"
    license = "GPL-2.0-only"
    description = "Generic Linux kernel headers"
    topics = ("linux", "headers", "generic")
    settings = "os", "arch", "build_type", "compiler"

    def package_id(self):
        del self.info.settings.os
        del self.info.settings.build_type
        del self.info.settings.compiler

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("linux-headers-generic supports only Linux")
        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration("linux-headers-generic can not be cross-compiled")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        with chdir(self, os.path.join(self.source_folder)):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.make(target="headers")

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "include/*.h", src=os.path.join(self.source_folder, "usr"))
