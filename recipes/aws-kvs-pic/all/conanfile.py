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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class awskvspicConan(ConanFile):
    name = "aws-kvs-pic"
    license = "Apache-2.0"
    homepage = "https://github.com/awslabs/amazon-kinesis-video-streams-pic"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Platform Independent Code for Amazon Kinesis Video Streams"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    topics = ("aws", "kvs", "kinesis", "video", "stream")

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        if self.settings.os != "Linux" and self.options.shared:
            raise ConanInvalidConfiguration("This library can only be built shared on Linux")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_DEPENDENCIES"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.components["kvspic"].libs = ["kvspic"]
        self.cpp_info.components["kvspic"].names["pkg_config"] = "libkvspic"
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["kvspic"].system_libs = ["dl", "rt", "pthread"]

        self.cpp_info.components["kvspicClient"].libs = ["kvspicClient"]
        self.cpp_info.components["kvspicClient"].names["pkg_config"] = "libkvspicClient"

        self.cpp_info.components["kvspicState"].libs = ["kvspicState"]
        self.cpp_info.components["kvspicState"].names["pkg_config"] = "libkvspicState"

        self.cpp_info.components["kvspicUtils"].libs = ["kvspicUtils"]
        self.cpp_info.components["kvspicUtils"].names["pkg_config"] = "libkvspicUtils"
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["kvspicUtils"].system_libs = ["dl", "rt", "pthread"]
