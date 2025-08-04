import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class OpenPMIxConan(ConanFile):
    name = "openpmix"
    description = "OpenPMIx: reference implementation of the Process Management Interface Exascale (PMIx) standard"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openpmix.github.io/"
    topics = ("process-management", "mpi", "openmpi", "pmix", "hpc")
    provides = ["pmix"]
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
        "with_curl": True,
        "with_jansson": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def config_options(self):
        if Version(self.version).major == 5:
            del self.options.with_curl
            del self.options.with_jansson

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # Used in a pmix/src/hwloc/pmix_hwloc.h public header
        self.requires("hwloc/[^2.11.1]", transitive_headers=True)
        self.requires("zlib-ng/[^2.0]")
        # Used in pmix/src/include/pmix_types.h public header
        self.requires("libevent/[^2.1.12]", transitive_headers=True)
        if self.options.get_safe("with_curl"):
            self.requires("libcurl/[>=7.78 <9]")
        if self.options.get_safe("with_jansson"):
            # v2.14 is not compatible as of v6.0.0
            self.requires("jansson/[~2.13.1]")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("OpenPMIx doesn't support Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualRunEnv(self).generate(scope="build")

        def root(pkg):
            return unix_path(self, self.dependencies[pkg].package_folder)

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic",
            "--exec-prefix=/",
            f"--with-hwloc={root('hwloc')}",
            f"--with-libevent={root('libevent')}",
            f"--with-zlib={root('zlib-ng')}",
            "--disable-sphinx",
            "--with-munge=no",
        ])
        if Version(self.version).major != 5:
            tc.configure_args.extend([
                f"--with-curl={root('libcurl') if self.options.with_curl else 'no'}",
                f"--with-jansson={root('jansson') if self.options.with_jansson else 'no'}",
            ])
        if self.settings.build_type in ["Debug", "RelWithDebInfo"]:
            tc.configure_args.append("--enable-debug-symbols")
        else:
            tc.configure_args.append("--disable-debug-symbols")
        if is_apple_os(self) and self.settings.arch == "armv8":
            tc.configure_args.append("--host=aarch64-apple-darwin")
            tc.extra_ldflags.append("-arch arm64")
        # libtool's libltdl is not really needed, OpenMPI provides its own equivalent.
        # Not adding it as it fails to be detected by ./configure in some cases.
        # https://github.com/open-mpi/ompi/blob/v4.1.6/opal/mca/dl/dl.h#L20-L25
        tc.configure_args.append("--with-libltdl=no")
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
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
        self.runenv_info.define_path("PMIX_DATADIR", os.path.join(self.package_folder, "share"))
        self.runenv_info.define_path("PMIX_DATAROOTDIR", os.path.join(self.package_folder, "share"))
