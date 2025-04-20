import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=2.1"


class DiligentToolsConan(ConanFile):
    name = "diligent-tools"
    description = "Diligent Core is a modern cross-platform low-level graphics API."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentTools/"
    topics = ("graphics", "texture", "gltf", "draco", "imgui")

    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "jpeg": [False, "libjpeg-turbo", "libjpeg"],
        "with_render_state_packager": [True, False],
        "with_archiver": [True, False],
    }
    default_options = {
        "jpeg": "libjpeg",
        "with_render_state_packager": False,
        "with_archiver": True,
    }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"diligent-core/{self.version}", transitive_headers=True, transitive_libs=True)
        self.requires("imgui/1.90.5", transitive_headers=True, transitive_libs=True)
        self.requires("imguizmo/cci.20231114")
        self.requires("libpng/[>=1.6 <2]")
        self.requires("libtiff/[>=4.5 <5]")
        self.requires("nlohmann_json/[^3.11]")
        self.requires("stb/cci.20250314")
        self.requires("taywee-args/6.4.6")
        self.requires("tinygltf/2.9.0")
        self.requires("zlib/[>=1.2.11 <2]")
        if self.options.jpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.jpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.1")

    def package_id(self):
        if is_msvc(self.info):
            if is_msvc_static_runtime(self.info):
                self.info.settings.compiler.runtime = "MT/MTd"
            else:
                self.info.settings.compiler.runtime = "MD/MDd"

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[^4]")
        # TODO: unvendor clang-format

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        rmdir(self, "ThirdParty")
        save(self, os.path.join("ThirdParty", "CMakeLists.txt"), "")
        replace_in_file(self, os.path.join("Imgui", "CMakeLists.txt"), "source_group(", "# source_group(")

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
        tc.cache_variables["CMAKE_PROJECT_DiligentTools_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["DILIGENT_INSTALL_TOOLS"] = False
        tc.cache_variables["DILIGENT_BUILD_SAMPLES"] = False
        tc.cache_variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.cache_variables["DILIGENT_BUILD_TESTS"] = False
        tc.cache_variables["DILIGENT_BUILD_TOOLS_TESTS"] = False
        tc.cache_variables["DILIGENT_BUILD_TOOLS_INCLUDE_TEST"] = False
        tc.cache_variables["DILIGENT_NO_RENDER_STATE_PACKAGER"] = not self.options.with_render_state_packager
        tc.cache_variables["ARCHIVER_SUPPORTED"] = not self.options.with_archiver
        tc.cache_variables["GL_SUPPORTED"] = True
        tc.cache_variables["GLES_SUPPORTED"] = True
        tc.cache_variables["VULKAN_SUPPORTED"] = True
        tc.cache_variables["METAL_SUPPORTED"] = True
        tc.cache_variables[self._diligent_platform] = True
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        copy(self, "*",
             os.path.join(self.dependencies["imgui"].package_folder, "res", "bindings"),
             os.path.join(self.source_folder, "Imgui", "src", "backends"))
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.hpp", self.source_folder, os.path.join(self.package_folder, "include", "DiligentTools"))
        copy(self, "*.dll", self.build_folder, os.path.join(self.package_folder, "bin"), keep_path=False)
        for pattern in ["*.lib", "*.a", "*.so", "*.dylib"]:
            copy(self, pattern, self.build_folder, os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"), keep_path=False)
        rmdir(self, os.path.join(self.package_folder, "Licenses"))
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

        # Copy missing includes
        copy(self, "*",
             os.path.join(self.source_folder, "TextureLoader", "interface"),
             os.path.join(self.package_folder, "include", "DiligentTools", "TextureLoader", "interface"))

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "AssetLoader", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "AssetLoader", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "Imgui", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "NativeApp", "include"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "RenderStateNotation", "include"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "RenderStatePackager", "include"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "Tests", "DiligentToolsTest", "include"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "TextureLoader", "include"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "TextureLoader", "interface"))

        self.cpp_info.defines.append(f"{self._diligent_platform}=1")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "pthread"]
        elif is_apple_os(self):
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa"]
