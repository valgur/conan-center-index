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

requires_conan_version = ">=1.33.0"


class I2cConan(ConanFile):
    name = "i2c-tools"
    license = "GPL-2.0-or-later", "LGPL-2.1"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://i2c.wiki.kernel.org/index.php/I2C_Tools"
    description = "I2C tools for the linux kernel as well as an I2C library."
    topics = "i2c"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("linux-headers-generic/5.14.9")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("i2c-tools only support Linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "Makefile"),
            "SRCDIRS	:= include lib eeprom stub tools $(EXTRA)",
            "SRCDIRS	:= include lib $(EXTRA)",
        )

    @property
    def _make_args(self):
        return [
            "PREFIX={}".format(self.package_folder),
            "BUILD_DYNAMIC_LIB={}".format("1" if self.options.shared else "0"),
            "BUILD_STATIC_LIB={}".format("0" if self.options.shared else "1"),
            "USE_STATIC_LIB={}".format("0" if self.options.shared else "1"),
        ]

    def build(self):
        self._patch_sources()
        autotools = AutoToolsBuildEnvironment(self)
        autotools.flags += [f"-I{path}" for path in autotools.include_paths]
        with chdir(self.source_folder):
            autotools.make(args=self._make_args)

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst="licenses")
        copy(self, "COPYING.LGPL", src=self.source_folder, dst="licenses")
        autotools = AutoToolsBuildEnvironment(self)
        autotools.flags += [f"-I{path}" for path in autotools.include_paths]
        with chdir(self.source_folder):
            autotools.install(args=self._make_args)
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["i2c"]
