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
from conan.tools.scm import Version
from conan.tools.system import package_manager
import os

required_conan_version = ">=1.47.0"


class SasscConan(ConanFile):
    name = "sassc"
    license = "MIT"
    homepage = "https://sass-lang.com/libsass"
    url = "https://github.com/conan-io/conan-center-index"
    description = "libsass command line driver"
    topics = ("Sass", "compiler")
    settings = "os", "compiler", "build_type", "arch"
    generators = "visual_studio"

    _autotools = None

    def config_options(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if not is_msvc(self) and self.info.settings.os not in ["Linux", "FreeBSD", "Macos"]:
            raise ConanInvalidConfiguration(
                "sassc supports only Linux, FreeBSD, Macos and Windows Visual Studio at this time, contributions are welcomed"
            )

    def requirements(self):
        self.requires("libsass/3.6.5")

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.build_folder, self.source_folder, "win", "sassc.vcxproj"),
            "$(LIBSASS_DIR)\\win\\libsass.targets",
            os.path.join(self.build_folder, "conanbuildinfo.props"),
        )

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        self._autotools.configure(args=["--disable-tests"])
        return self._autotools

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
                self.run("{} -fiv".format(get_env(self, "AUTORECONF")), run_environment=True)
                save(self, path="VERSION", content=f"{self.version}")
                autotools = self._configure_autotools()
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
                autotools = self._configure_autotools()
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
