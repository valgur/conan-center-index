# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    copy,
    export_conandata_patches,
    get,
    rm,
    rmdir,
)
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=1.53.0"


class DiligentToolsConan(ConanFile):
    name = "diligent-tools"
    description = "Diligent Core is a modern cross-platfrom low-level graphics API."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentTools/"
    topics = ("graphics", "texture", "gltf", "draco", "imgui")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "jpeg": [False, "libjpeg-turbo", "libjpeg"],
        "with_render_state_packager": [True, False],
        "with_archiver": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "jpeg": "libjpeg",
        "with_render_state_packager": False,
        "with_archiver": True,
    }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "BuildUtils.cmake", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.version == "cci.20211009":
            self.requires("diligent-core/2.5.1")
            self.requires("imgui/1.87")
        else:
            self.requires("diligent-core/{}".format(self.version))
            self.requires("taywee-args/6.3.0")
            self.requires("imgui/1.85")

        if self.options.jpeg == "libjpeg":
            self.requires("libjpeg/9e")
        if self.options.jpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/2.1.4")
        self.requires("libpng/1.6.37")
        self.requires("libtiff/4.3.0")
        self.requires("zlib/1.2.12")

    def package_id(self):
        if is_msvc(self):
            if not is_msvc_static_runtime(self):
                self.info.settings.compiler.runtime = "MD/MDd"
            else:
                self.info.settings.compiler.runtime = "MT/MTd"

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.options.shared:
            raise ConanInvalidConfiguration("Can't build diligent tools as shared lib")

    def build_requirements(self):
        self.tool_requires("cmake/3.24.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

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
        tc.variables["DILIGENT_INSTALL_TOOLS"] = False
        tc.variables["DILIGENT_BUILD_SAMPLES"] = False
        tc.variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.variables["DILIGENT_BUILD_TESTS"] = False
        tc.variables["DILIGENT_BUILD_TOOLS_TESTS"] = False
        tc.variables["DILIGENT_BUILD_TOOLS_INCLUDE_TEST"] = False
        tc.variables["DILIGENT_NO_RENDER_STATE_PACKAGER"] = not self.options.with_render_state_packager
        tc.variables["ARCHIVER_SUPPORTED"] = not self.options.with_archiver
        if (
            self.version != "cci.20211009"
            and (self.version.startswith("api") and self.version >= "api.252005")
            or (self.version > "2.5.2")
        ):
            tc.variables["GL_SUPPORTED"] = True
            tc.variables["GLES_SUPPORTED"] = True
            tc.variables["VULKAN_SUPPORTED"] = True
            tc.variables["METAL_SUPPORTED"] = True
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
        copy(
            self,
            "*.hpp",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "include/DiligentTools"),
            keep_path=True,
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
        copy(
            self,
            "*",
            src=os.path.join(self.build_folder, "bin"),
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )
        rmdir(self, os.path.join(self.package_folder, "Licenses"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "AssetLoader", "interface"))

        self.cpp_info.defines.append(f"{self._diligent_platform}=1")

        if self.settings.os in ["Macos", "Linux"]:
            self.cpp_info.system_libs = ["dl", "pthread"]
        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa"]
