# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import chdir, copy, get, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class OpenMPIConan(ConanFile):
    name = "openmpi"
    description = "A High Performance Message Passing Library"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.open-mpi.org"
    topics = ("mpi", "openmpi")

    package_type = "library"
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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("OpenMPI doesn't support Windows")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # FIXME : self.requires("libevent/2.1.12") - try to use libevent from conan
        self.requires("zlib/1.2.11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.generate()
        args = ["--disable-wrapper-rpath", "--disable-wrapper-runpath"]
        if self.settings.build_type == "Debug":
            args.append("--enable-debug")
        args.append("--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic")
        args.append("--enable-mpi-fortran={}".format(str(self.options.fortran)))
        args.append("--with-zlib={}".format(self.dependencies["zlib"].cpp_info.rootpath))
        args.append("--with-zlib-libdir={}".format(self.dependencies["zlib"].cpp_info.libdirs[0]))
        args.append("--datarootdir=${prefix}/res")
        tc.configure_args += args

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(
            self, pattern="LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses")
        )
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rm(self, "*.la", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.libs = ["mpi", "open-rte", "open-pal"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "pthread", "rt", "util"]

        self.output.info(f"Creating MPI_HOME environment variable: {self.package_folder}")
        self.env_info.MPI_HOME = self.package_folder
        self.output.info(f"Creating OPAL_PREFIX environment variable: {self.package_folder}")
        self.env_info.OPAL_PREFIX = self.package_folder
        mpi_bin = os.path.join(self.package_folder, "bin")
        self.output.info(f"Creating MPI_BIN environment variable: {mpi_bin}")
        self.env_info.MPI_BIN = mpi_bin
        self.output.info(f"Appending PATH environment variable: {mpi_bin}")
        self.env_info.PATH.append(mpi_bin)
