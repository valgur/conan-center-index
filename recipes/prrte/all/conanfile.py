import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.files.symlinks import absolute_to_relative_symlinks
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class PrrteConan(ConanFile):
    name = "prrte"
    description = "PMIx Reference RunTime Environment (PRRTE)"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openpmix.github.io/"
    topics = ("process-management", "mpi", "openmpi", "pmix", "hpc")
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
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openpmix/[^6.0.0]")
        self.requires("hwloc/[^2.11.1]")
        self.requires("libevent/[^2.1.12]")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("PRRTE doesn't support Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualRunEnv(self).generate(scope="build")

        def root(pkg):
            return self.dependencies[pkg].package_folder

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic",
            "--exec-prefix=/",
            "--enable-ipv6",
            "--disable-sphinx",
            f"--with-pmix={root('openpmix')}",
            "--disable-pmix-lib-checks",
            f"--with-hwloc={root('hwloc')}",
            f"--with-libevent={root('libevent')}",
            "--with-munge=no",
        ])
        if self.settings.build_type in ["Debug", "RelWithDebInfo"]:
            tc.configure_args.append("--enable-debug-symbols")
        else:
            tc.configure_args.append("--disable-debug-symbols")
        if is_apple_os(self) and self.settings.arch == "armv8":
            tc.configure_args.append("--host=aarch64-apple-darwin")
            tc.extra_ldflags.append("-arch arm64")
        tc.configure_args.append("--with-libltdl=no")
        deps = AutotoolsDeps(self)
        env = deps.environment.vars(self)
        # Linking of static transitive deps for tools is broken without this
        tc.make_args.append(f'LIBS={env["LDFLAGS"]} {env["LIBS"]}')
        deps.generate()
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", self.package_folder, recursive=True)
        absolute_to_relative_symlinks(self, os.path.join(self.package_folder, "bin"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = ["prrte"]
        self.cpp_info.includedirs.append("include/prte")
        self.cpp_info.resdirs = ["etc"]
