import os
import shutil

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"

class DiligentFxConan(ConanFile):
    name = "diligent-fx"
    description = "DiligentFX is the Diligent Engine's high-level rendering framework."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentFx/"
    topics = ("graphics", "game-engine", "renderer", "graphics-library")

    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"diligent-tools/{self.version}", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    @property
    def _diligent_platform(self):
        return {
            "Android": "PLATFORM_ANDROID",
            "Emscripten": "PLATFORM_EMSCRIPTEN",
            "Linux": "PLATFORM_LINUX",
            "Macos": "PLATFORM_MACOS",
            "Windows": "PLATFORM_WIN32",
            "iOS": "PLATFORM_IOS",
            "watchOS": "PLATFORM_TVOS",
        }.get(str(self.settings.os))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.variables["DILIGENT_BUILD_TESTS"] = False
        tc.variables[self._diligent_platform] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        rename(self, os.path.join(self.package_folder, "include", "source_subfolder"), os.path.join(self.package_folder, "include", "DiligentFx"))
        shutil.move(os.path.join(self.package_folder, "Shaders"), os.path.join(self.package_folder, "res", "Shaders"))
        copy(self, "*.dll", self.build_folder, os.path.join(self.package_folder, "bin"), keep_path=False)
        for pattern in ["*.lib", "*.a", "*.so", "*.dylib"]:
            copy(self, pattern, self.build_folder, os.path.join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx", "Components", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx", "GLTF_PBR_Renderer", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentFx", "PostProcess", "EpipolarLightScattering", "interface"))
        self.cpp_info.includedirs.append(os.path.join("res"))
