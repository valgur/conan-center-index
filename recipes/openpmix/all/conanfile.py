import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=2.1"


class OpenPMIxConan(ConanFile):
    name = "openpmix"
    description = "OpenPMIx: reference implementation of the Process Management Interface Exascale (PMIx) standard"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openpmix.github.io/"
    topics = ("process-management", "mpi", "openmpi")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_curl": [True, False],
        "with_jansson": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_curl": False,
        "with_jansson": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # Used in a pmix/src/hwloc/pmix_hwloc.h public header
        self.requires("hwloc/2.11.1", transitive_headers=True)
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("libevent/2.1.12")
        if self.options.get_safe("with_curl"):
            self.requires("libcurl/[>=7.78 <9]")
        if self.options.get_safe("with_jansson"):
            # v2.14 is not compatible as of v5.0.3
            self.requires("jansson/2.13.1")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("OpenPMIx doesn't support Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def generate(self):
        VirtualRunEnv(self).generate(scope="build")

        def root(pkg):
            return unix_path(self, self.dependencies[pkg].package_folder)

        tc = AutotoolsToolchain(self)
        tc.configure_args += [
            "--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic",
            "--exec-prefix=/",
            "--datarootdir=${prefix}/res",
            f"--with-hwloc={root('hwloc')}",
            f"--with-libevent={root('libevent')}",
            f"--with-zlib={root('zlib')}",
            f"--with-curl={root('libcurl') if self.options.with_curl else 'no'}",
            f"--with-jansson={root('jansson') if self.options.with_jansson else 'no'}",
            "--disable-sphinx",
            "--with-alps=no",
            "--with-cxi=no",
            "--with-lustre=no",
            "--with-munge=no",
        ]
        if self.settings.build_type in ["Debug", "RelWithDebInfo"]:
            tc.configure_args.append("--enable-debug-symbols")
        else:
            tc.configure_args.append("--disable-debug-symbols")
        if is_apple_os(self):
            if self.settings.arch == "armv8":
                tc.configure_args.append("--host=aarch64-apple-darwin")
                tc.extra_ldflags.append("-arch arm64")
        # libtool's libltdl is not really needed, OpenMPI provides its own equivalent.
        # Not adding it as it fails to be detected by ./configure in some cases.
        # https://github.com/open-mpi/ompi/blob/v4.1.6/opal/mca/dl/dl.h#L20-L25
        tc.configure_args.append("--with-libltdl=no")
        tc.generate()

    @property
    def _source_subdir(self):
        return os.path.join(self.source_folder, f"pmix-{self.version}")

    def build(self):
        autotools = Autotools(self)
        autotools.configure(build_script_folder=self._source_subdir)
        autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self._source_subdir, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "res", "doc"))
        rmdir(self, os.path.join(self.package_folder, "res", "man"))
        rm(self, "*.la", self.package_folder, recursive=True)
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "pmix")
        self.cpp_info.libs = ["pmix"]

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
        self.runenv_info.define_path("PMIX_PREFIX", self.package_folder)
        self.runenv_info.define_path("PMIX_EXEC_PREFIX", self.package_folder)
        self.runenv_info.define_path("PMIX_LIBDIR", os.path.join(self.package_folder, "lib"))
        self.runenv_info.define_path("PMIX_DATADIR", os.path.join(self.package_folder, "res"))
        self.runenv_info.define_path("PMIX_DATAROOTDIR", os.path.join(self.package_folder, "res"))
