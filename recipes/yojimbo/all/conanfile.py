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
import yaml


class YojimboConan(ConanFile):
    name = "yojimbo"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/networkprotocol/yojimbo"
    topics = ("yojimbo", "game", "udp", "protocol", "client-server", "multiplayer-game-server")
    description = "A network library for client/server games written in C++"
    license = "BSD-3-Clause"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }

    def export_sources(self):
        copy(self, "submoduledata.yml", src=self.recipe_folder, dst=self.export_sources_folder)

    def configure(self):
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only 64-bit architecture supported")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("libsodium/1.0.18")
        self.requires("mbedtls/2.25.0")

    def build_requirements(self):
        self.tool_requires("premake/5.0.0-alpha15")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

        submodule_filename = os.path.join(self.recipe_folder, "submoduledata.yml")
        with open(submodule_filename, "r") as submodule_stream:
            submodules_data = yaml.load(submodule_stream)
            for path, submodule in submodules_data["submodules"][self.version].items():
                submodule_data = {
                    "url": submodule["url"],
                    "sha256": submodule["sha256"],
                    "destination": os.path.join(self.source_folder, submodule["destination"]),
                    "strip_root": True,
                }

                get(self, **submodule_data)
                submodule_source = os.path.join(self.source_folder, path)
                rmdir(self, submodule_source)

    def build(self):
        # Before building we need to make some edits to the premake file to build using conan dependencies rather than local/bundled

        # Generate the list of dependency include and library paths as strings
        include_path_str = ", ".join(
            f'"{p}"'
            for p in self.deps_cpp_info["libsodium"].include_paths
            + self.deps_cpp_info["mbedtls"].include_paths
        )
        lib_path_str = ", ".join(
            f'"{p}"'
            for p in self.deps_cpp_info["libsodium"].lib_paths + self.deps_cpp_info["mbedtls"].lib_paths
        )

        premake_path = os.path.join(self.source_folder, "premake5.lua")

        if self.settings.os == "Windows":
            # Replace Windows directory seperator
            include_path_str = include_path_str.replace("\\", "/")
            lib_path_str = lib_path_str.replace("\\", "/")

            # Edit the premake script to use conan rather than bundled dependencies
            replace_in_file(
                self,
                premake_path,
                'includedirs { ".", "./windows"',
                'includedirs { ".", %s' % include_path_str,
                strict=True,
            )
            replace_in_file(
                self, premake_path, 'libdirs { "./windows" }', "libdirs { %s }" % lib_path_str, strict=True
            )

            # Edit the premake script to change the name of libsodium
            replace_in_file(self, premake_path, '"sodium"', '"libsodium"', strict=True)

        else:
            # Edit the premake script to use  conan rather than local dependencies
            replace_in_file(self, premake_path, '"/usr/local/include"', include_path_str, strict=True)

        # Build using premake

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

        with chdir(self.source_folder):
            self.run("premake5 %s" % generator)

            if self.settings.compiler == "Visual Studio":
                msbuild = MSBuild(self)
                msbuild.build("Yojimbo.sln")
            else:
                config = "debug" if self.settings.build_type == "Debug" else "release"
                config += "_x64"
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make(args=["config=%s" % config])

    def package(self):
        copy(
            self, pattern="LICENCE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        copy(
            self,
            pattern="yojimbo.h",
            dst=os.path.join(self.package_folder, "include"),
            src=self.source_folder,
        )

        copy(self, pattern="*/yojimbo.lib", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, pattern="*/libyojimbo.a", dst=os.path.join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
