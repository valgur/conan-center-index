import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, VCVars

required_conan_version = ">=2.4"


class MakeConan(ConanFile):
    name = "make"
    description = (
        "GNU Make is a tool which controls the generation of executables and "
        "other non-source files of a program from the program's source files"
    )
    topics = ("make", "build", "makefile")
    homepage = "https://www.gnu.org/software/make/"
    url = "https://github.com/conan-io/conan-center-index"
    license = "GPL-3.0-or-later"
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "i18n": [True, False],
    }
    default_options = {
        "i18n": False,
    }
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.i18n

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self.options.get_safe("i18n"):
            self.tool_requires("gettext/[>=0.21 <1]")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if is_msvc(self):
            vcvars = VCVars(self)
            vcvars.generate()
        if self.settings_build.os != "Windows":
            tc = AutotoolsToolchain(self)
            tc.configure_args.append("--enable-nls" if self.options.i18n else "--disable-nls")
            tc.generate()

    def build(self):
        if self.settings_build.os == "Windows":
            # README.W32
            if is_msvc(self):
                self.run("build_w32.bat --without-guile", cwd=self.source_folder)
            else:
                self.run("build_w32.bat --without-guile gcc", cwd=self.source_folder)
        else:
            autotools = Autotools(self)
            autotools.configure()
            if self.options.i18n:
                with chdir(self, os.path.join(self.build_folder, "po")):
                    autotools.make()
            self.run("./build.sh")

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if self.options.get_safe("i18n"):
            with chdir(self, os.path.join(self.build_folder, "po")):
                autotools = Autotools(self)
                autotools.install()
        for make_exe in ("make", "*gnumake.exe"):
            src = self.source_folder if self.settings_build.os == "Windows" else self.build_folder
            copy(self, make_exe, src, os.path.join(self.package_folder, "bin"), keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        if self.options.get_safe("i18n"):
            self.cpp_info.resdirs = ["share"]

        make = os.path.join(self.package_folder, "bin", "gnumake.exe" if self.settings.os == "Windows" else "make")
        self.conf_info.define("tools.gnu:make_program", make)
