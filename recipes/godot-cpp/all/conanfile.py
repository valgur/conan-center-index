# Warnings:
#   Unexpected method '_bits'
#   Unexpected method '_custom_api_file'
#   Unexpected method '_headers_dir'
#   Unexpected method '_platform'
#   Unexpected method '_target'
#   Unexpected method '_use_llvm'
#   Unexpected method '_use_mingw'
#   Unexpected method '_libname'
#   Unexpected method '_godot_headers'
#   Missing required method 'config_options'
#   Missing required method 'configure'
#   Missing required method 'generate'

# TODO: verify the Conan v2 migration

import glob
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

required_conan_version = ">=1.53.0"


class GodotCppConan(ConanFile):
    name = "godot-cpp"
    description = "C++ bindings for the Godot script API"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/godotengine/godot-cpp"
    topics = ("game-engine", "game-development", "c++")

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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("godot_headers/{}".format(self.version))

    def package_id(self):
        if self._target == "release":
            self.info.settings.build_type = "Release"
        else:
            self.info.settings.build_type = "Debug"

    def validate(self):
        minimal_cpp_standard = 14
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)

        minimal_version = {
            "gcc": "5",
            "clang": "4",
            "apple-clang": "10",
            "Visual Studio": "15",
        }

        compiler = str(self.settings.compiler)
        if compiler not in minimal_version:
            self.output.warn(
                f"{self.name} recipe lacks information about the {compiler} compiler standard version support"
            )
            self.output.warn(
                f"{self.name} requires a compiler that supports at least C++{minimal_cpp_standard}"
            )
            return

        version = Version(self.settings.compiler.version)
        if version < minimal_version[compiler]:
            if compiler in ["apple-clang", "clang"]:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires a clang version that supports the '-Og' flag"
                )
            raise ConanInvalidConfiguration(
                f"{self.name} requires a compiler that supports at least C++{minimal_cpp_standard}"
            )

    def build_requirements(self):
        self.tool_requires("scons/3.1.2")

    @property
    def _bits(self):
        return 64 if self.settings.get_safe("arch") in ["x86_64", "armv8"] else 32

    @property
    def _custom_api_file(self):
        return "{}/api.json".format(self._godot_headers.res_paths[0])

    @property
    def _headers_dir(self):
        return self._godot_headers.include_paths[0]

    @property
    def _platform(self):
        flag_map = {
            "Windows": "windows",
            "Linux": "linux",
            "Macos": "osx",
        }
        return flag_map[self.settings.get_safe("os")]

    @property
    def _target(self):
        return "debug" if self.settings.get_safe("build_type") == "Debug" else "release"

    @property
    def _use_llvm(self):
        return self.settings.get_safe("compiler") in ["clang", "apple-clang"]

    @property
    def _use_mingw(self):
        return self._platform == "windows" and self.settings.compiler == "gcc"

    @property
    def _libname(self):
        return "godot-cpp.{platform}.{target}.{bits}".format(
            platform=self._platform, target=self._target, bits=self._bits
        )

    @property
    def _godot_headers(self):
        return self.deps_cpp_info["godot_headers"]

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rename(self, glob.glob("godot-cpp-*")[0], self.source_folder)

    def generate(self):
        # TODO: fill in generate()
        pass

    def build(self):
        self.run("python  --version")
        if self.settings.os == "Macos":
            self.run("which python")
        self.run("scons  --version")
        self.run(
            " ".join(
                [
                    "scons",
                    f"-C{self.source_folder}",
                    f"-j{cpu_count(self)}",
                    "generate_bindings=yes",
                    "use_custom_api_file=yes",
                    f"bits={self._bits}",
                    f"custom_api_file={self._custom_api_file}",
                    f"headers_dir={self._headers_dir}",
                    f"platform={self._platform}",
                    f"target={self._target}",
                    f"use_llvm={self._use_llvm}",
                    f"use_mingw={self._use_mingw}",
                ]
            )
        )

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*.hpp",
            dst=os.path.join(self.package_folder, "include/godot-cpp"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(
            self,
            "*.a",
            dst=os.path.join(self.package_folder, "lib"),
            src=os.path.join(self.source_folder, "bin"),
        )
        copy(
            self,
            "*.lib",
            dst=os.path.join(self.package_folder, "lib"),
            src=os.path.join(self.source_folder, "bin"),
        )

    def package_info(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = [f"lib{self._libname}"]
        else:
            self.cpp_info.libs = [self._libname]

        self.cpp_info.includedirs = [
            os.path.join("include", "godot-cpp"),
            os.path.join("include", "godot-cpp", "core"),
            os.path.join("include", "godot-cpp", "gen"),
        ]
