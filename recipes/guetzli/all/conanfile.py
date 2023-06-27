# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, chdir, copy, get, export_conandata_patches
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.microsoft import MSBuild, MSBuildToolchain, is_msvc

required_conan_version = ">=1.47.0"


class GoogleGuetzliConan(ConanFile):
    name = "guetzli"
    description = "Perceptual JPEG encoder"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opensource.google/projects/guetzli"
    topics = ("jpeg", "compression", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        pass

    def requirements(self):
        self.requires("libpng/1.6.37")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if self.settings.os not in ["Linux", "Windows"]:
            raise ConanInvalidConfiguration(
                f"conan recipe for guetzli v{self.version} is not available in {self.settings.os}."
            )
        if self.settings.compiler.get_safe("libcxx") == "libc++":
            raise ConanInvalidConfiguration(
                f"conan recipe for guetzli v{self.version} cannot be built with libc++"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            tc.make_args = ["config=release", "verbose=1',"]
            tc.generate()

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            msbuild = MSBuild(self)
            with chdir(self, self.source_folder):
                msbuild.build("guetzli.sln", build_type="Release")
        else:
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        if is_msvc(self):
            copy(
                self,
                os.path.join(self.source_folder, "bin", str(self.settings.arch), "Release", "guetzli.exe"),
                dst=os.path.join(self.package_folder, "bin"),
                src=self.build_folder,
                keep_path=False,
            )
        else:
            copy(
                self,
                os.path.join(self.source_folder, "bin", "Release", "guetzli"),
                dst=os.path.join(self.package_folder, "bin"),
                src=self.build_folder,
                keep_path=False,
            )
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(bindir)
