import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, msvc_runtime_flag, check_min_vs, unix_path

required_conan_version = ">=2.4"


class IslConan(ConanFile):
    name = "isl"
    description = "isl is a library for manipulating sets and relations of integer points bounded by linear constraints."
    topics = ("isl", "integer", "set", "library")
    license = "MIT"
    homepage = "https://libisl.sourceforge.io"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_int": ["gmp", "imath", "imath-32"],
        "autogen": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_int": "gmp",
        "autogen": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("Cannot build shared isl library on Windows (due to libtool refusing to link to static/import libraries)")
        if msvc_runtime_flag(self) == "MDd" and not check_min_vs(self, 192, raise_invalid=False):
            # isl fails to link with this version of visual studio and MDd runtime:
            # gmp.lib(bdiv_dbm1c.obj) : fatal error LNK1318: Unexpected PDB error; OK (0)
            raise ConanInvalidConfiguration("isl cannot be built with MDd runtime with MSVC < 192")

    def requirements(self):
        if self.options.with_int == "gmp":
            self.requires("gmp/6.3.0")
        elif self.options.with_int == "imath":
            self.requires("imath/3.1.9")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if self.options.autogen:
            self.tool_requires("libtool/[^2.4.7]")

    def package_id(self):
        del self.info.options.autogen

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args.append(f'--with-int={self.options.with_int}')
        tc.configure_args.append("--enable-portable-binary")
        if self.options.with_int == "gmp":
            tc.configure_args.append("--with-gmp=system")
            tc.configure_args.append(f'--with-gmp-prefix={unix_path(self, self.dependencies["gmp"].package_folder)}')
        if is_msvc(self):
            if check_min_vs(self, 191, raise_invalid=False):
                tc.extra_cflags.append("-Zf")
        # ./configure tries to find a more specific compiler executable with
        # a triplet in its name and can fail if CC_FOR_BUILD is not set.
        build_cc = tc.vars().get("CC_FOR_BUILD" if cross_building(self) else "CC", "cc")
        tc.configure_args.append(f"CC_FOR_BUILD={build_cc}")
        env = tc.environment()
        if is_msvc(self):
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
        tc.generate(env)

    def build(self):
        autotools = Autotools(self)
        if self.options.autogen:
            autotools.autoreconf()
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(os.path.join(self.package_folder, "lib")))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "isl")
        self.cpp_info.libs = ["isl"]
