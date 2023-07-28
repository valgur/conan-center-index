# TODO: verify the Conan v2 migration

import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import chdir, copy, get, replace_in_file, rm
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import MSBuild, MSBuildToolchain, is_msvc

required_conan_version = ">=1.53.0"


class LibId3TagConan(ConanFile):
    name = "libid3tag"
    description = "ID3 tag manipulation library."
    license = "GPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.underbit.com/products/mad/"
    topics = ("mad", "id3", "MPEG", "audio", "decoder")

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
        self.requires("zlib/1.2.13")

    def validate(self):
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration("libid3tag does not support shared library for MSVC")

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("gnu-config/cci.20210814")
            if self._settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            tc.generate()
            tc = PkgConfigDeps(self)
            tc.generate()

    def build(self):
        if is_msvc(self):
            self._build_msvc()
        else:
            self._build_autotools()

    def _build_msvc(self):
        kwargs = {}
        with chdir(self, os.path.join(self.source_folder, "msvc++")):
            # cl : Command line error D8016: '/ZI' and '/Gy-' command-line options are incompatible
            replace_in_file(self, "libid3tag.dsp", "/ZI ", "")
            if self.settings.compiler == "clang":
                replace_in_file(self, "libid3tag.dsp", "CPP=cl.exe", "CPP=clang-cl.exe")
                replace_in_file(self, "libid3tag.dsp", "RSC=rc.exe", "RSC=llvm-rc.exe")
                kwargs["toolset"] = "ClangCl"
            if self.settings.arch == "x86_64":
                replace_in_file(self, "libid3tag.dsp", "Win32", "x64")
            with vcvars(self.settings):
                self.run("devenv /Upgrade libid3tag.dsp")
            msbuild = MSBuild(self)
            msbuild.build(project_file="libid3tag.vcxproj", **kwargs)

    def _build_autotools(self):
        shutil.copy(
            self.conf_info.get("user.gnu-config:CONFIG_SUB"), os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self.conf_info.get("user.gnu-config:CONFIG_GUESS"),
            os.path.join(self.source_folder, "config.guess"),
        )
        autotools = Autotools(self)
        autotools.make()

    def _install_autotools(self):
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)

    def package(self):
        copy(self, "COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "CREDITS", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if is_msvc(self):
            copy(
                self,
                pattern="*.lib",
                dst=os.path.join(self.package_folder, "lib"),
                src=self.source_folder,
                keep_path=False,
            )
            copy(
                self,
                pattern="id3tag.h",
                dst=os.path.join(self.package_folder, "include"),
                src=self.source_folder,
            )
        else:
            self._install_autotools()

    def package_info(self):
        self.cpp_info.libs = ["libid3tag" if is_msvc(self) else "id3tag"]
