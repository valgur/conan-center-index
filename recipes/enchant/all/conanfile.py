import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv, Environment
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, chdir, replace_in_file
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps, Autotools, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path
from conans import ConanFile, tools, AutoToolsBuildEnvironment
import contextlib
import os
import shutil

required_conan_version = ">=1.53.0"


class EnchantConan(ConanFile):
    name = "enchant"
    description = ("Enchant aims to provide a simple but comprehensive abstraction for "
                   "dealing with different spell-checking libraries in a consistent way")
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://abiword.github.io/enchant/"
    topics = ("enchant", "spell", "spell-check")

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

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("glib/2.77.0")
        self.requires("hunspell/1.7.0")

    def build_requirements(self):
        self.tool_requires("libtool/2.4.7")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if is_msvc(self):
            self.tool_requires("automake/1.16.5")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/1.9.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.generate()
        return
        env = VirtualBuildEnv(self)
        env.generate()
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate()

        tc = AutotoolsToolchain(self)
        tc.generate()
        deps = AutotoolsDeps(self)
        deps.generate()

        if is_msvc(self):
            env = Environment()
            automake_conf = self.dependencies.build["automake"].conf_info
            compile_wrapper = unix_path(self, automake_conf.get("user.automake:compile-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            # ar-lib wrapper is added automatically by ./configure
            # env.define("AR", f'{ar_wrapper} "lib -nologo"')
            env.define("NM", "dumpbin -symbols")
            env.define("OBJDUMP", ":")
            env.define("RANLIB", ":")
            env.define("STRIP", ":")
            env.vars(self).save_script("conanbuild_msvc")

    @contextlib.contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            automake_conf = self.dependencies.build["automake"].conf_info
            compile_wrapper = unix_path(self, automake_conf.get("user.automake:compile-wrapper", check_type=str))
            with tools.vcvars(self):
                env = {
                    "AR": "{} lib".format(tools.unix_path(os.path.join(self.build_folder, "build-aux", "ar-lib"))),
                    "CC": f"{compile_wrapper} cl -nologo",
                    "CXX": f"{compile_wrapper} cl -nologo",
                    "LD": "link -nologo",
                    "NM": "dumpbin -symbols",
                    "OBJDUMP": ":",
                    "RANLIB": ":",
                    "STRIP": ":",
                }
                with tools.environment_append(env):
                    yield
        else:
            yield

    def build(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "configure.ac"), "AX_CXX_COMPILE_STDCXX(11)", "")
        with chdir(self, self.source_folder):
            with self._build_context():
                os.environ["M4"] = ""
                self.run("{} -fiv".format(os.environ["AUTORECONF"]))
                autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                replace_in_file(self, os.path.join(self.source_folder, "configure"), "# Be more", "set -x #")
                autotools.configure()
                autotools.make()

    def package(self):
        copy(self, "COPYING.LIB", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()

    def package_info(self):
        self.cpp_info.libs = ["enchant"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl"]
