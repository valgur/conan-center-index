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


class WafConan(ConanFile):
    name = "waf"
    description = "The Waf build system"
    topics = "builsystem"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://waf.io"
    license = "BSD-3-Clause"
    settings = "os", "arch"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("waf-{}".format(self.version), self.source_folder)

    @property
    def _license_text(self):
        [_, license, _] = open(os.path.join(self.source_folder, "waf"), "rb").read().split(b'"""', 3)
        return license.decode().lstrip()

    def build(self):
        pass

    def package(self):
        binpath = os.path.join(self.package_folder, "bin")
        libpath = os.path.join(self.package_folder, "lib")

        os.mkdir(binpath)
        os.mkdir(libpath)

        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._license_text)

        copy(self, "waf", src=self.source_folder, dst=binpath)
        copy(self, "waf-light", src=self.source_folder, dst=binpath)
        copy(self, "waflib/*", src=self.source_folder, dst=libpath)

        if self.settings.os == "Windows":
            copy(self, "waf.bat", src=os.path.join(self.source_folder, "utils"), dst=binpath)

        os.chmod(os.path.join(binpath, "waf"), 0o755)
        os.chmod(os.path.join(binpath, "waf-light"), 0o755)

    def package_info(self):
        self.cpp_info.libdirs = []

        binpath = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var: {}".format(binpath))
        self.env_info.PATH.append(binpath)

        wafdir = os.path.join(self.package_folder, "lib")
        self.output.info("Setting WAFDIR env var: {}".format(wafdir))
        self.env_info.WAFDIR = wafdir
