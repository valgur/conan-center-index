# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import chdir, copy, get, replace_in_file, save
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import MSBuild, is_msvc

required_conan_version = ">=1.53.0"


class SasscConan(ConanFile):
    name = "sassc"
    description = "libsass command line driver"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sass-lang.com/libsass"
    topics = ("Sass", "compiler")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def config_options(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libsass/3.6.5")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if not is_msvc(self) and self.info.settings.os not in ["Linux", "FreeBSD", "Macos"]:
            raise ConanInvalidConfiguration(
                "sassc supports only Linux, FreeBSD, Macos and Windows Visual Studio at this time,"
                " contributions are welcomed"
            )

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args = ["--disable-tests"]
        tc.generate()

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.build_folder, self.source_folder, "win", "sassc.vcxproj"),
            "$(LIBSASS_DIR)\\win\\libsass.targets",
            os.path.join(self.build_folder, "conanbuildinfo.props"),
        )

    def _build_msbuild(self):
        msbuild = MSBuild(self)
        platforms = {
            "x86": "Win32",
            "x86_64": "Win64",
        }
        msbuild.build("win/sassc.sln", platforms=platforms)

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            if is_msvc(self):
                self._build_msbuild()
            else:
                save(self, path="VERSION", content=f"{self.version}")
                autotools = Autotools(self)
                autotools.autoreconf()
                autotools.configure()
                autotools.make()

    def package(self):
        with chdir(self, self.source_folder):
            if is_msvc(self):
                copy(
                    self,
                    "*.exe",
                    dst=os.path.join(self.package_folder, "bin"),
                    src=os.path.join(self.source_folder, "bin"),
                    keep_path=False,
                )
            else:
                autotools = Autotools(self)
                autotools.install()
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bin_folder = os.path.join(self.package_folder, "bin")
        # TODO: Legacy, to be removed on Conan 2.0
        self.env_info.PATH.append(bin_folder)
