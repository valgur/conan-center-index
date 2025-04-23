import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path, is_msvc

required_conan_version = ">=2.1"


class AutoconfConan(ConanFile):
    name = "autoconf"
    description = (
        "Autoconf is an extensible package of M4 macros that produce shell "
        "scripts to automatically configure software source code packages"
    )
    license = ("GPL-2.0-or-later", "GPL-3.0-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/autoconf/"
    topics = ("configure", "build")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("m4/1.4.19") # Needed at runtime by downstream clients as well

    def package_id(self):
        self.info.clear()

    def build_requirements(self):
        self.tool_requires("m4/1.4.19")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "Makefile.in"),
                        "M4 = /usr/bin/env m4", "#M4 = /usr/bin/env m4")
        if self.settings_build.os == "Windows":
            # Handle vagaries of Windows line endings
            replace_in_file(self, os.path.join(self.source_folder, "bin", "autom4te.in"),
                            "$result =~ s/^\\n//mg;", "$result =~ s/^\\R//mg;")

    def generate(self):
        tc = AutotoolsToolchain(self)

        if self.settings.os == "Windows":
            if is_msvc(self):
                build = "{}-{}-{}".format(
                    "x86_64" if self.settings_build.arch == "x86_64" else "i686",
                    "pc" if self.settings_build.arch == "x86" else "win64",
                    "mingw32")
                host = "{}-{}-{}".format(
                    "x86_64" if self.settings.arch == "x86_64" else "i686",
                    "pc" if self.settings.arch == "x86" else "win64",
                    "mingw32")
                tc.configure_args.append(f"--build={build}")
                tc.configure_args.append(f"--host={host}")

        env = tc.environment()
        env.define_path("INSTALL", unix_path(self, os.path.join(self.source_folder, "build-aux", "install-sh")))
        tc.generate(env)

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        rmdir(self, os.path.join(self.package_folder, "share", "info"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = ["share"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.buildenv_info.define_path("AUTOCONF", os.path.join(bin_path, "autoconf"))
        self.buildenv_info.define_path("AUTORECONF", os.path.join(bin_path, "autoreconf"))
        self.buildenv_info.define_path("AUTOHEADER", os.path.join(bin_path, "autoheader"))
        self.buildenv_info.define_path("AUTOM4TE", os.path.join(bin_path, "autom4te"))
