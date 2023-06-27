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


class TarConan(ConanFile):
    name = "tar"
    description = (
        "GNU Tar provides the ability to create tar archives, as well as various other kinds of manipulation."
    )
    topics = "archive"
    license = "GPL-3-or-later"
    homepage = "https://www.gnu.org/software/tar/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("bzip2/1.0.8")
        self.requires("lzip/1.21")
        self.requires("xz_utils/5.2.5")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "This recipe does not support Windows builds of tar"
            )  # FIXME: fails on MSVC and mingw-w64
        if not self.options["bzip2"].build_executable:
            raise ConanInvalidConfiguration("bzip2:build_executable must be enabled")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.generate()
        self._autotools.libs = []
        bzip2_exe = "bzip2"  # FIXME: get from bzip2 recipe
        lzip_exe = "lzip"  # FIXME: get from lzip recipe
        lzma_exe = "lzma"  # FIXME: get from xz_utils recipe
        xz_exe = "xz"  # FIXME: get from xz_utils recipe
        args = [
            "--disable-acl",
            "--disable-nls",
            "--disable-rpath",
            # "--without-gzip",  # FIXME: this will use system gzip
            "--without-posix-acls",
            "--without-selinux",
            "--with-bzip2={}".format(bzip2_exe),
            "--with-lzip={}".format(lzip_exe),
            "--with-lzma={}".format(lzma_exe),
            # "--without-lzop",  # FIXME: this will use sytem lzop
            "--with-xz={}".format(xz_exe),
            # "--without-zstd",  # FIXME: this will use system zstd (current zstd recipe does not build programs)
        ]
        self._autotools.configure(args=args, configure_dir=self.source_folder)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            replace_in_file(
                self,
                os.path.join(self.source_folder, "gnu", "faccessat.c"),
                "_GL_INCLUDING_UNISTD_H",
                "_GL_INCLUDING_UNISTD_H_NOP",
            )
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        tar_bin = os.path.join(self.package_folder, "bin", "tar")
        self.user_info.tar = tar_bin
        self.env_info.TAR = tar_bin
