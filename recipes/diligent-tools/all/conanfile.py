import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get, rm, rmdir, replace_in_file
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
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        copy(self, "BuildUtils.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"diligent-core/{self.version}")
        self.requires("taywee-args/6.4.6")
        self.requires("imgui/1.90")

        if self.options.jpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.jpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.1")
        self.requires("libpng/1.6.40")
        self.requires("libtiff/4.6.0")
        self.requires("zlib/[>=1.2.11 <2]")

    def package_id(self):
        if is_msvc(self.info):
            if not is_msvc_static_runtime(self.info):
                self.info.settings.compiler.runtime = "MD/MDd"
            else:
                self.info.settings.compiler.runtime = "MT/MTd"

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.options.shared:
            raise ConanInvalidConfiguration("Can't build diligent tools as shared lib")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _diligent_platform(self):
        if self.settings.os == "Windows":
            return "PLATFORM_WIN32"
        elif is_apple_os(self):
            return "PLATFORM_MACOS"
        elif self.settings.os in ["Linux", "FreeBSD"]:
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
        venv = VirtualBuildEnv(self)
        venv.generate()

        tc = CMakeToolchain(self)
        tc.variables["DILIGENT_INSTALL_TOOLS"] = False
        tc.variables["DILIGENT_BUILD_SAMPLES"] = False
        tc.variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.variables["DILIGENT_BUILD_TESTS"] = False
        tc.variables["DILIGENT_BUILD_TOOLS_TESTS"] = False
        tc.variables["DILIGENT_BUILD_TOOLS_INCLUDE_TEST"] = False
        tc.variables["DILIGENT_NO_RENDER_STATE_PACKAGER"] = not self.options.with_render_state_packager
        tc.variables["ARCHIVER_SUPPORTED"] = not self.options.with_archiver
        tc.variables["GL_SUPPORTED"] = True
        tc.variables["GLES_SUPPORTED"] = True
        tc.variables["VULKAN_SUPPORTED"] = True
        tc.variables["METAL_SUPPORTED"] = True
        tc.variables[self._diligent_platform] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "cmake_minimum_required (VERSION 3.6)",
                        "cmake_minimum_required (VERSION 3.15)\n"
                        "project(DiligentTools CXX)\n"
                        "include(conan_deps.cmake)\n")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.hpp",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "include/DiligentTools"))
        copy(self, "*.dll",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, "bin"),
             keep_path=False)
        for pattern in ["*.lib", "*.a", "*.so", "*.dylib"]:
            copy(self, pattern,
                 src=self.build_folder,
                 dst=os.path.join(self.package_folder, "lib"),
                 keep_path=False)
        copy(self, "*",
             src=os.path.join(self.build_folder, "bin"),
             dst=os.path.join(self.package_folder, "bin"),
             keep_path=False)
        rmdir(self, os.path.join(self.package_folder, "Licenses"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools"))
        self.cpp_info.includedirs.append(os.path.join("include", "DiligentTools", "AssetLoader", "interface"))

        self.cpp_info.defines.append(f"{self._diligent_platform}=1")

        if self.settings.os in ["Linux", "FreeBSD"] or is_apple_os(self):
            self.cpp_info.system_libs = ["dl", "pthread"]
        if is_apple_os(self):
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa"]
