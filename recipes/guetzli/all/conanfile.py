# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import apply_conandata_patches, chdir, copy, get, export_conandata_patches
from conan.tools.microsoft import MSBuild, is_msvc


class GoogleGuetzliConan(ConanFile):
    name = "guetzli"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opensource.google/projects/guetzli"
    description = "Perceptual JPEG encoder"
    topics = ("jpeg", "compression")
    settings = "os", "compiler", "arch"
    generators = "pkg_config"

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        self.requires("libpng/1.6.37")

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
        extracted_dir = "guetzli-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            msbuild = MSBuild(self)
            with chdir(self, self.source_folder):
                msbuild.build("guetzli.sln", build_type="Release")
        else:
            autotools = AutoToolsBuildEnvironment(self)
            with chdir(self, self.source_folder):
                env_vars = {"PKG_CONFIG_PATH": self.build_folder}
                env_vars.update(autotools.vars)
                with environment_append(self, env_vars):
                    make_args = ["config=release", "verbose=1',"]
                    autotools.make(args=make_args)

    def package(self):
        if is_msvc(self):
            copy(
                self,
                os.path.join(self.source_folder, "bin", str(self.settings.arch), "Release", "guetzli.exe"),
                dst=os.path.join(self.package_folder, "bin"),
                keep_path=False,
            )
        else:
            copy(
                self,
                os.path.join(self.source_folder, "bin", "Release", "guetzli"),
                dst=os.path.join(self.package_folder, "bin"),
                keep_path=False,
            )
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(bindir)
