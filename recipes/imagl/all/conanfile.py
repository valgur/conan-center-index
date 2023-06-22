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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class ImaglConan(ConanFile):
    name = "imagl"
    license = "GPL-3.0-or-later"
    homepage = "https://github.com/Woazim/imaGL"
    url = "https://github.com/conan-io/conan-center-index"
    description = "A lightweight library to load image for OpenGL application."
    topics = ("opengl", "texture", "image")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_png": [True, False],
        "with_jpeg": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_png": True,
        "with_jpeg": True,
    }

    @property
    def _compilers_minimum_version(self):
        minimum_versions = {
            "gcc": "9",
            "Visual Studio": "16.2",
            "msvc": "19.22",
            "clang": "10",
            "apple-clang": "11",
        }
        if Version(self.version) <= "0.1.1" or Version(self.version) == "0.2.0":
            minimum_versions["Visual Studio"] = "16.5"
            minimum_versions["msvc"] = "19.25"
        return minimum_versions

    @property
    def _supports_jpeg(self):
        return Version(self.version) >= "0.2.0"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not self._supports_jpeg:
            self.options.rm_safe("with_jpeg")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        if self.options.with_png:
            self.requires("libpng/1.6.37")
        if self._supports_jpeg and self.options.with_jpeg:
            self.requires("libjpeg/9d")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 20)

        def lazy_lt_semver(v1, v2):
            lv1 = [int(v) for v in v1.split(".")]
            lv2 = [int(v) for v in v2.split(".")]
            min_length = min(len(lv1), len(lv2))
            return lv1[:min_length] < lv2[:min_length]

        # Special check for clang that can only be linked to libc++
        if self.settings.compiler == "clang" and self.settings.compiler.libcxx != "libc++":
            raise ConanInvalidConfiguration(
                "imagl requires some C++20 features, which are available in libc++ for clang compiler."
            )

        compiler_version = str(self.settings.compiler.version)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warn("imaGL requires C++20. Your compiler is unknown. Assuming it supports C++20.")
        elif lazy_lt_semver(compiler_version, minimum_version):
            raise ConanInvalidConfiguration(
                "imaGL requires some C++20 features, which your"
                f" {str(self.settings.compiler)} {compiler_version} compiler does not support."
            )
        else:
            print(f"Your compiler is {str(self.settings.compiler)} {compiler_version} and is compatible.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["STATIC_LIB"] = not self.options.shared
        tc.variables["SUPPORT_PNG"] = self.options.with_png
        tc.variables["SUPPORT_JPEG"] = self._supports_jpeg and self.options.with_jpeg
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        debug_suffix = "d" if self.settings.build_type == "Debug" else ""
        static_suffix = "" if self.options.shared else "s"
        self.cpp_info.libs = ["imaGL{}{}".format(debug_suffix, static_suffix)]
        if not self.options.shared:
            self.cpp_info.defines = ["IMAGL_STATIC=1"]
