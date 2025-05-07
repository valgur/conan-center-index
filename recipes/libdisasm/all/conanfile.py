import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.4"


class LibdisasmConan(ConanFile):
    name = "libdisasm"
    description = "The libdisasm library provides basic disassembly of Intel x86 instructions from a binary stream."
    homepage = "http://bastard.sourceforge.net/libdisasm.html"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("disassembler", "x86", "asm")
    license = "MIT"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("libtool/[^2.4.7]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = AutotoolsToolchain(self)
        env = tc.environment()
        if is_msvc(self):
            automake_conf = self.dependencies.build["automake"].conf_info
            ar_wrapper = unix_path(self, automake_conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
            env.define("CPP", "cl -E -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.define("STRIP", ":")
            env.define("RANLIB", ":")
        tc.generate(env)

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        autotools.make()
        if self.settings.os != "Windows":
            autotools.make(args=["-C", "x86dis"])

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        if self.settings.os != "Windows":
            autotools.install(args=["-C", "x86dis"])
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)
        if is_msvc(self) and self.options.shared:
            dlllib = os.path.join(self.package_folder, "lib", "disasm.dll.lib")
            if os.path.exists(dlllib):
                rename(self, dlllib, os.path.join(self.package_folder, "lib", "disasm.lib"))

    def package_info(self):
        self.cpp_info.libs = ["disasm"]
