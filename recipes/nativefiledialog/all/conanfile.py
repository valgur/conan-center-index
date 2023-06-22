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

class NativefiledialogConan(ConanFile):
    name = "nativefiledialog"
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mlabbe/nativefiledialog"
    description = "A tiny, neat C library that portably invokes native file open and save dialogs."
    topics = ("dialog", "gui")
    settings = "os", "compiler", "build_type", "arch"
    generators = ("pkg_config",)

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("gtk/3.24.24")

    def build_requirements(self):
        self.build_requires("premake/5.0.0-alpha15")

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

        if self.settings.arch not in ["x86", "x86_64"]:
            raise ConanInvalidConfiguration("architecture %s is not supported" % self.settings.arch)

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-release_" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            generator = "vs" + {
                "16": "2019",
                "15": "2017",
                "14": "2015",
                "12": "2013",
                "11": "2012",
                "10": "2010",
                "9": "2008",
                "8": "2005",
            }.get(str(self.settings.compiler.version))
        else:
            generator = "gmake2"
        subdir = os.path.join(self._source_subfolder, "build", "subdir")
        os.makedirs(subdir)
        with tools.chdir(subdir):
            os.rename(os.path.join("..", "premake5.lua"), "premake5.lua")
            self.run("premake5 %s" % generator)

            if self.settings.compiler == "Visual Studio":
                msbuild = MSBuild(self)
                msbuild.build("NativeFileDialog.sln")
            else:
                config = "debug" if self.settings.build_type == "Debug" else "release"
                config += "_x86" if self.settings.arch == "x86" else "_x64"
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make(args=["config=%s" % config])

    def package(self):
        libname = "nfd_d" if self.settings.build_type == "Debug" else "nfd"
        if self.settings.compiler == "Visual Studio":
            self.copy("*%s.lib" % libname, dst="lib", src=self._source_subfolder, keep_path=False)
        else:
            self.copy("*%s.a" % libname, dst="lib", src=self._source_subfolder, keep_path=False)
        self.copy("*nfd.h", dst="include", src=self._source_subfolder, keep_path=False)
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        self.cpp_info.libs = ["nfd_d" if self.settings.build_type == "Debug" else "nfd"]
