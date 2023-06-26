# Warnings:
#   Missing required method 'generate'

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
from conan.tools.files import get, rmdir, rm, copy, rename
from conan.tools.scm import Version
from conan.tools.build import check_min_cppstd
from conan.errors import ConanInvalidConfiguration
import os

required_conan_version = ">=1.53.0"


class UvmSystemC(ConanFile):
    name = "accellera-uvm-systemc"
    description = "Universal Verification Methodology for SystemC"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://systemc.org/about/systemc-verification/uvm-systemc-faq"
    topics = ("systemc", "verification", "tlm", "uvm")

    package_type = "library"
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

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("systemc/2.3.3")

    def validate(self):
        if self.settings.os == "Macos":
            raise ConanInvalidConfiguration("Macos build not supported")
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Windows build not yet supported")
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "7":
            raise ConanInvalidConfiguration("GCC < version 7 is not supported")

    def build_requirements(self):
        self.tool_requires("cmake/3.24.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def build(self):
        autotools = AutoToolsBuildEnvironment(self)
        args = [f"--with-systemc={self.deps_cpp_info['systemc'].rootpath}"]
        if self.options.shared:
            args.extend(["--enable-shared", "--disable-static"])
        else:
            args.extend(["--enable-static", "--disable-shared"])
        autotools.configure(configure_dir=self.source_folder, args=args)
        autotools.make()

    def package(self):
        copy(
            self,
            "LICENSE",
            src=os.path.join(self.build_folder, self.source_folder),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "NOTICE",
            src=os.path.join(self.build_folder, self.source_folder),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "COPYING",
            src=os.path.join(self.build_folder, self.source_folder),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        autotools = AutoToolsBuildEnvironment(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "docs"))
        rmdir(self, os.path.join(self.package_folder, "examples"))
        rm(self, "AUTHORS", self.package_folder)
        rm(self, "COPYING", self.package_folder)
        rm(self, "ChangeLog", self.package_folder)
        rm(self, "LICENSE", self.package_folder)
        rm(self, "NOTICE", self.package_folder)
        rm(self, "NEWS", self.package_folder)
        rm(self, "RELEASENOTES", self.package_folder)
        rm(self, "README", self.package_folder)
        rm(self, "INSTALL", self.package_folder)
        rename(
            self, os.path.join(self.package_folder, "lib-linux64"), os.path.join(self.package_folder, "lib")
        )
        rm(self, "libuvm-systemc.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libs = ["uvm-systemc"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
