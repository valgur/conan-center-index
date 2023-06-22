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


required_conan_version = ">=1.52.0"


class DiligentFxConan(ConanFile):
    name = "diligent-fx"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentFx/"
    description = "DiligentFX is the Diligent Engine's high-level rendering framework."
    license = "Apache-2.0"
    topics = ("graphics", "game-engine", "renderer", "graphics-library")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    generators = "cmake_find_package", "cmake"

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt")
        copy(self, "BuildUtils.cmake")
        copy(self, "script.py")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def validate(self):
        if self.options.shared:
            raise ConanInvalidConfiguration("Can't build as a shared lib")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        if self.version == "cci.20220219" or self.version == "cci.20211112":
            self.requires("diligent-tools/2.5.2")
        else:
            self.requires("diligent-tools/{}".format(self.version))

    @property
    def _diligent_platform(self):
        if self.settings.os == "Windows":
            return "PLATFORM_WIN32"
        elif self.settings.os == "Macos":
            return "PLATFORM_MACOS"
        elif self.settings.os == "Linux":
            return "PLATFORM_LINUX"
        elif self.settings.os == "Android":
            return "PLATFORM_ANDROID"
        elif self.settings.os == "iOS":
            return "PLATFORM_IOS"
        elif self.settings.os == "Emscripten":
            return "PLATFORM_EMSCRIPTEN"
        elif self.settings.os == "watchOS":
            return "PLATFORM_TVOS"

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.variables["DILIGENT_BUILD_TESTS"] = False

        tc.variables[self._diligent_platform] = True
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "License.txt", dst="licenses", src=self.source_folder)
        rename(
            self,
            src=os.path.join(self.package_folder, "include", "source_subfolder"),
            dst=os.path.join(self.package_folder, "include", "DiligentFx"),
        )
        shutil.move(
            os.path.join(self.package_folder, "Shaders"), os.path.join(self.package_folder, "res", "Shaders")
        )

        copy(self, pattern="*.dll", src=self.build_folder, dst="bin", keep_path=False)
        copy(self, pattern="*.dylib", src=self.build_folder, dst="lib", keep_path=False)
        copy(self, pattern="*.lib", src=self.build_folder, dst="lib", keep_path=False)
        copy(self, pattern="*.a", src=self.build_folder, dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx", "Components", "interface"))
        self.cpp_info.includedirs.append(
            os.path.join("include", "DiligentFx", "GLTF_PBR_Renderer", "interface")
        )
        self.cpp_info.includedirs.append(
            os.path.join("include", "DiligentFx", "PostProcess", "EpipolarLightScattering", "interface")
        )
        self.cpp_info.includedirs.append(os.path.join("res"))
