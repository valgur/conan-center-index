# TODO: verify the Conan v2 migration

import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    copy,
    export_conandata_patches,
    get,
    rename,
)

required_conan_version = ">=1.53.0"


class DiligentFxConan(ConanFile):
    name = "diligent-fx"
    description = "DiligentFX is the Diligent Engine's high-level rendering framework."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentFx/"
    topics = ("graphics", "game-engine", "renderer", "graphics-library")

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

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "BuildUtils.cmake", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "script.py", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.version == "cci.20220219" or self.version == "cci.20211112":
            self.requires("diligent-tools/2.5.2")
        else:
            self.requires("diligent-tools/{}".format(self.version))

    def validate(self):
        if self.options.shared:
            raise ConanInvalidConfiguration("Can't build as a shared lib")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _diligent_platform(self):
        if self.settings.os == "Windows":
            return "PLATFORM_WIN32"
        elif is_apple_os(self):
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
        cmake.configure(build_script_folder=self.source_path.parent)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rename(
            self,
            src=os.path.join(self.package_folder, "include", "source_subfolder"),
            dst=os.path.join(self.package_folder, "include", "DiligentFx"),
        )
        shutil.move(
            os.path.join(self.package_folder, "Shaders"), os.path.join(self.package_folder, "res", "Shaders")
        )

        copy(
            self,
            pattern="*.dll",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )

        for pattern in ["*.lib", "*.a", "*.so", "*.dylib"]:
            copy(
                self,
                pattern,
                src=self.build_folder,
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )

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
