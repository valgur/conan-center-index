# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
import os


class GoogleGuetzliConan(ConanFile):
    name = "guetzli"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opensource.google/projects/guetzli"
    description = "Perceptual JPEG encoder"
    topics = ("jpeg", "compression")
    exports_sources = "patches/**"
    settings = "os", "compiler", "arch"
    generators = "pkg_config"
    requires = ["libpng/1.6.37"]

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def configure(self):
        if self.settings.os not in ["Linux", "Windows"]:
            raise ConanInvalidConfiguration(
                "conan recipe for guetzli v{0} is not \
                available in {1}.".format(
                    self.version, self.settings.os
                )
            )

        if self.settings.compiler.get_safe("libcxx") == "libc++":
            raise ConanInvalidConfiguration(
                "conan recipe for guetzli v{0} cannot be\
                built with libc++".format(
                    self.version
                )
            )

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "guetzli-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _patch_sources(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def build(self):
        self._patch_sources()
        if self._is_msvc:
            msbuild = MSBuild(self)
            with tools.chdir(self._source_subfolder):
                msbuild.build("guetzli.sln", build_type="Release")
        else:
            autotools = AutoToolsBuildEnvironment(self)
            with tools.chdir(self._source_subfolder):
                env_vars = {"PKG_CONFIG_PATH": self.build_folder}
                env_vars.update(autotools.vars)
                with tools.environment_append(env_vars):
                    make_args = ["config=release", "verbose=1',"]
                    autotools.make(args=make_args)

    def package(self):
        if self._is_msvc:
            self.copy(
                os.path.join(
                    self._source_subfolder, "bin", str(self.settings.arch), "Release", "guetzli.exe"
                ),
                dst="bin",
                keep_path=False,
            )
        else:
            self.copy(
                os.path.join(self._source_subfolder, "bin", "Release", "guetzli"), dst="bin", keep_path=False
            )
        self.copy("LICENSE", src=self._source_subfolder, dst="licenses")

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
