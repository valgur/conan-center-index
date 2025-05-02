import os

from conan import ConanFile
from conan.tools import CppInfo
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import Environment, VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.4"


class FliteConan(ConanFile):
    name = "flite"
    description = "A small fast portable speech synthesis system"
    license = "MIT AND Apache-2.0 AND BSD-3-Clause AND Public-Domain AND BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/festvox/flite"
    topics = ("speech", "synthesis", "tts", "text-to-speech")
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
        self.requires("libalsa/[~1.2.10]")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
            if is_msvc(self):
                self.tool_requires("automake/[^1.16.5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        tc.generate()

        if is_msvc(self):
            env = Environment()
            automake_conf = self.dependencies.build["automake"].conf_info
            compile_wrapper = unix_path(self, automake_conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, automake_conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.vars(self).save_script("conanbuild_msvc")

        if is_msvc(self):
            cpp_info = CppInfo(self)
            for dependency in self.dependencies.values():
                cpp_info.merge(dependency.cpp_info.aggregated_components())
            env = Environment()
            env.append("CPPFLAGS", [f"-I{unix_path(self, p)}" for p in cpp_info.includedirs] + [f"-D{d}" for d in cpp_info.defines])
            env.append("_LINK_", [lib if lib.endswith(".lib") else f"{lib}.lib" for lib in cpp_info.libs])
            env.append("LDFLAGS", [f"-L{unix_path(self, p)}" for p in cpp_info.libdirs] + cpp_info.sharedlinkflags + cpp_info.exelinkflags)
            env.append("CFLAGS", cpp_info.cflags)
            env.vars(self).save_script("conanautotoolsdeps_cl_workaround")
        else:
            deps = AutotoolsDeps(self)
            deps.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
            rm(self, "*.lib", os.path.join(self.package_folder, "lib"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "flite"))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "m", "pthread"])
