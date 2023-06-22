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


class LibisalConan(ConanFile):
    name = "isa-l"
    description = "Intel's Intelligent Storage Acceleration Library"
    license = "BSD-3"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/intel/isa-l"
    topics = "compression"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def validate(self):
        if self.settings.arch not in ["x86", "x86_64", "armv8"]:
            raise ConanInvalidConfiguration("CPU Architecture not supported")
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("Only Linux and FreeBSD builds are supported")

    def build_requirements(self):
        self.tool_requires("libtool/2.4.6")
        self.tool_requires("nasm/2.15.05")

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        with chdir(self.source_folder):
            self.run("./autogen.sh")
            env_build = AutoToolsBuildEnvironment(self)
            extra_args = list()
            if self.options.shared:
                extra_args.extend(("--enable-static=no",))
            else:
                extra_args.extend(("--enable-shared=no",))
            env_build.configure(".", args=extra_args, build=False, host=False, target=False)
            env_build.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst="licenses")
        copy(self, "*/isa-l.h", dst="include/isa-l", keep_path=False)
        copy(self, "*.h", dst="include/isa-l", src="%s/include" % (self.source_folder), keep_path=False)
        if self.options.shared:
            copy(self, "*.dll", dst="bin", keep_path=False)
            copy(self, "*.so*", dst="lib", keep_path=False, symlinks=True)
            copy(self, "*.dylib", dst="lib", keep_path=False)
        else:
            copy(self, "*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
