# Warnings:
#   Unexpected method '_configure_autotools'
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
import os

required_conan_version = ">=1.53.0"


class LibfabricConan(ConanFile):
    name = "aws-libfabric"
    description = "AWS Libfabric"
    license = ("BSD-2-Clause", "GPL-2.0-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/aws/libfabric"
    topics = ("fabric", "communication", "framework", "service")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "gni": [True, False, "shared"],
        "psm": [True, False, "shared"],
        "psm2": [True, False, "shared"],
        "sockets": [True, False, "shared"],
        "rxm": [True, False, "shared"],
        "tcp": [True, False, "shared"],
        "udp": [True, False, "shared"],
        "usnic": [True, False, "shared"],
        "verbs": [True, False, "shared"],
        "bgq": [True, False, "shared"],
        "shm": [True, False, "shared"],
        "efa": [True, False, "shared"],
        "rxd": [True, False, "shared"],
        "mrail": [True, False, "shared"],
        "rstream": [True, False, "shared"],
        "perf": [True, False, "shared"],
        "hook_debug": [True, False, "shared"],
        "with_libnl": [True, False],
        "bgq_progress": ["auto", "manual"],
        "bgq_mr": ["basic", "scalable"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "gni": False,
        "psm": False,
        "psm2": False,
        "sockets": False,
        "rxm": False,
        "tcp": True,
        "udp": False,
        "usnic": False,
        "verbs": False,
        "bgq": False,
        "shm": False,
        "efa": False,
        "rxd": False,
        "mrail": False,
        "rstream": False,
        "perf": False,
        "hook_debug": False,
        "with_libnl": False,
        "bgq_progress": "manual",
        "bgq_mr": "basic",
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        elif self.settings.os == "Linux":
            self.options.efa = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_libnl:
            self.requires("libnl/3.2.25")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("The libfabric package cannot be built on Windows.")

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        with chdir(self, self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")))

        yes_no_dl = lambda v: {
            "True": "yes",
            "False": "no",
            "shared": "dl",
        }[str(v)]
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--with-bgq-progress={}".format(self.options.bgq_progress),
            "--with-bgq-mr={}".format(self.options.bgq_mr),
        ]
        for p in self._providers:
            args.append("--enable-{}={}".format(p, yes_no_dl(getattr(self.options, p))))
        if self.options.with_libnl:
            args.append("--with-libnl={}".format(unix_path(self, self.dependencies["libnl"].package_folder))),
        else:
            args.append("--with-libnl=no")
        if self.settings.build_type == "Debug":
            args.append("--enable-debug")
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        autotools = Autotools(self)
        autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "libfabric"
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["pthread", "m"]
            if not self.options.shared:
                self.cpp_info.system_libs.extend(["dl", "rt"])
