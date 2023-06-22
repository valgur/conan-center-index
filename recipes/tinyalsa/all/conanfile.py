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


class TinyAlsaConan(ConanFile):
    name = "tinyalsa"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/tinyalsa/tinyalsa"
    topics = ("tiny", "alsa", "sound", "audio", "tinyalsa")
    description = "A small library to interface with ALSA in the Linux kernel"
    exports_sources = ["patches/*"]
    options = {
        "shared": [True, False],
        "with_utils": [True, False],
    }
    default_options = {
        "shared": False,
        "with_utils": False,
    }
    settings = "os", "compiler", "build_type", "arch"

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("{} only works for Linux.".format(self.name))

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)
        with chdir(self.source_folder):
            env_build = AutoToolsBuildEnvironment(self)
            env_build.make()

    def package(self):
        copy(self, "NOTICE", dst="licenses", src=self.source_folder)

        with chdir(self.source_folder):
            env_build = AutoToolsBuildEnvironment(self)
            env_build_vars = env_build.vars
            env_build_vars["PREFIX"] = self.package_folder
            env_build.install(vars=env_build_vars)

        rmdir(self, os.path.join(self.package_folder, "share"))

        if not self.options.with_utils:
            rmdir(self, os.path.join(self.package_folder, "bin"))

        with chdir(self, os.path.join(self.package_folder, "lib")):
            files = os.listdir()
            for f in files:
                if (self.options.shared and f.endswith(".a")) or (
                    not self.options.shared and not f.endswith(".a")
                ):
                    os.unlink(f)

    def package_info(self):
        self.cpp_info.libs = ["tinyalsa"]
        if Version(self.version) >= "2.0.0":
            self.cpp_info.system_libs.append("dl")
        if self.options.with_utils:
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info("Appending PATH environment variable: %s" % bin_path)
            self.env_info.path.append(bin_path)
