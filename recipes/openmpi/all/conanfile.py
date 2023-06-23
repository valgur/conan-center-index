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

required_conan_version = ">=1.29.1"


class OpenMPIConan(ConanFile):
    name = "openmpi"
    homepage = "https://www.open-mpi.org"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("mpi", "openmpi")
    description = "A High Performance Message Passing Library"
    license = "BSD-3-Clause"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "fortran": ["yes", "mpifh", "usempi", "usempi80", "no"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "fortran": "no",
    }

    _autotools = None

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("OpenMPI doesn't support Windows")

    def requirements(self):
        # FIXME : self.requires("libevent/2.1.12") - try to use libevent from conan
        self.requires("zlib/1.2.11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        args = ["--disable-wrapper-rpath", "--disable-wrapper-runpath"]
        if self.settings.build_type == "Debug":
            args.append("--enable-debug")
        if self.options.shared:
            args.extend(["--enable-shared", "--disable-static"])
        else:
            args.extend(["--enable-static", "--disable-shared"])
        args.append("--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic")
        args.append("--enable-mpi-fortran={}".format(str(self.options.fortran)))
        args.append("--with-zlib={}".format(self.dependencies["zlib"].cpp_info.rootpath))
        args.append("--with-zlib-libdir={}".format(self.dependencies["zlib"].cpp_info.libdirs[0]))
        args.append("--datarootdir=${prefix}/res")
        self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(
            self, pattern="LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses")
        )
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["mpi", "open-rte", "open-pal"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl", "pthread", "rt", "util"]

        self.output.info("Creating MPI_HOME environment variable: {}".format(self.package_folder))
        self.env_info.MPI_HOME = self.package_folder
        self.output.info("Creating OPAL_PREFIX environment variable: {}".format(self.package_folder))
        self.env_info.OPAL_PREFIX = self.package_folder
        mpi_bin = os.path.join(self.package_folder, "bin")
        self.output.info("Creating MPI_BIN environment variable: {}".format(mpi_bin))
        self.env_info.MPI_BIN = mpi_bin
        self.output.info("Appending PATH environment variable: {}".format(mpi_bin))
        self.env_info.PATH.append(mpi_bin)
