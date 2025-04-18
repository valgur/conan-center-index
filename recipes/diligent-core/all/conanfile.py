import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc

required_conan_version = ">=2.1"


class DiligentCoreConan(ConanFile):
    name = "diligent-core"
    description = "Diligent Core is a modern cross-platform low-level graphics API."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/DiligentCore"
    topics = ("graphics",)
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC":   [True, False],
        "with_glslang": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_glslang": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def package_id(self):
        if is_msvc(self.info):
            if is_msvc_static_runtime(self.info):
                self.info.settings.compiler.runtime = "MT/MTd"
            else:
                self.info.settings.compiler.runtime = "MD/MDd"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opengl/system")
        self.requires("glew/2.2.0")
        if self.settings.os == "Linux":
            self.requires("wayland/1.22.0")

        self.requires("spirv-headers/1.4.309.0")
        self.requires("spirv-cross/1.4.309.0", options={"shared": False})
        self.requires("spirv-tools/1.4.309.0")
        if self.options.with_glslang:
            self.requires("glslang/1.4.309.0")
        self.requires("vulkan-headers/1.4.309.0")
        self.requires("vulkan-validationlayers/1.4.309.0")
        self.requires("volk/1.4.309.0")
        self.requires("xxhash/[>=0.8.1 <0.9]")
        # TODO: unvendor DirectXShaderCompiler headers?
        # TODO: unvendor DXBCChecksum from FidelityFX-SDK?

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("xorg/system")
            if can_run(self):
                self.requires("xkbcommon/1.6.0")

    def validate(self):
        check_min_cppstd(self, 14)
        if is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration("Visual Studio build with MT runtime is not supported")
        if self._diligent_platform is None:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.dependencies["spirv-cross"].options.shared:
            # Otherwise fails with many spirv_cross::Compiler::* linker errors in SPIRVShaderResources.cpp
            raise ConanInvalidConfiguration("spirv-cross must be built as static (-o spirv-cross/*:shared=False)")

    def build_requirements(self):
        self.tool_requires("cmake/[^4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Remove vendored libs, except for two minor ones without a Conan package
        third_party = Path(self.source_folder, "ThirdParty")
        third_party.joinpath("CMakeLists.txt").write_text("")
        for path in third_party.iterdir():
            if path.is_dir() and path.name not in ["DirectXShaderCompiler", "GPUOpenShaderUtils"]:
                rmdir(self, path)
        # Always install core files: fix android and emscripten installations
        replace_in_file(self, "CMakeLists.txt",
                        "set(DILIGENT_INSTALL_CORE OFF)",
                        "set(DILIGENT_INSTALL_CORE ON)")

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
        tc.cache_variables["CMAKE_PROJECT_DiligentCore_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_SHARED_LIBS"] = False  # both static and shared are always built
        tc.cache_variables["DILIGENT_BUILD_SAMPLES"] = False
        tc.cache_variables["DILIGENT_NO_FORMAT_VALIDATION"] = True
        tc.cache_variables["DILIGENT_BUILD_TESTS"] = False
        tc.cache_variables["DILIGENT_NO_DXC"] = True
        tc.cache_variables["DILIGENT_NO_GLSLANG"] = not self.options.with_glslang
        tc.cache_variables["DILIGENT_USE_SPIRV_TOOLCHAIN"] = True
        tc.cache_variables["DILIGENT_CLANG_COMPILE_OPTIONS"] = ""
        tc.cache_variables["DILIGENT_MSVC_COMPILE_OPTIONS"] = ""
        tc.cache_variables["ENABLE_RTTI"] = True
        tc.cache_variables["ENABLE_EXCEPTIONS"] = True
        tc.cache_variables[self._diligent_platform] = True
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.19"
        tc.cache_variables["SPIRV_CROSS_NAMESPACE_OVERRIDE"] = self.dependencies["spirv-cross"].options.namespace
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("glew", "cmake_target_name", "GLEW::glew")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rename(self, os.path.join(self.package_folder, "Licenses"), os.path.join(self.package_folder, "licenses"))
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "bin"))
        if self.options.shared:
            copy(self, "*.dylib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
            copy(self, "*.so", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
            copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), src=self.build_folder, keep_path=False)
            rm(self, os.path.join(self.package_folder, "lib"), "*.a", recursive=True)
            if self.settings.os != "Windows":
                rm(self, os.path.join(self.package_folder, "lib"), "*.lib", recursive=True)
        else:
            copy(self, "*.a",   dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
            copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
            rm(self, os.path.join(self.package_folder, "lib"), "*.dylib", recursive=True)
            rm(self, os.path.join(self.package_folder, "lib"), "*.so", recursive=True)
            rm(self, os.path.join(self.package_folder, "lib"), "*.dll", recursive=True)

        copy(self, "*.fxh", dst=os.path.join(self.package_folder, "res"), src=self.source_folder, keep_path=False)
        copy(self, "File2String*",  dst=os.path.join(self.package_folder, "bin"), src=self.source_folder, keep_path=False)
        rm(self, "*.pdb", self.package_folder, recursive=True)
        # MinGw creates many invalid files, called objects.a, remove them here:
        rm(self, "objects.a", self.package_folder, recursive=True)

        # BuildUtils.cmake is required in diligent-tools and others, but is not packaged correctly by DiligentCore
        copy(self, "BuildUtils.cmake",
             dst=os.path.join(self.package_folder, "lib", "cmake"),
             src=os.path.join(self.source_folder, "BuildTools", "CMake", "BuildUtils.cmake"))

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.resdirs = ["res"]

        # included as discussed here https://github.com/conan-io/conan-center-index/pull/10732#issuecomment-1123596308
        self.cpp_info.includedirs = [
            os.path.join("include"),
            os.path.join("include", "Common"),
            os.path.join("include", "Common", "interface"),
            os.path.join("include", "Platforms", "interface"),
            os.path.join("include", "Graphics", "GraphicsEngine", "interface"),
            os.path.join("include", "Graphics", "GraphicsEngineVulkan", "interface"),
            os.path.join("include", "Graphics", "GraphicsEngineOpenGL", "interface"),
            os.path.join("include", "Graphics", "GraphicsAccessories", "interface"),
            os.path.join("include", "Graphics", "GraphicsTools", "interface"),
            os.path.join("include", "Graphics", "HLSL2GLSLConverterLib", "interface"),
        ]

        archiver_path = os.path.join("include", "Graphics", "Archiver", "interface")
        if os.path.isdir(archiver_path):
            self.cpp_info.includedirs.append(archiver_path)

        self.cpp_info.includedirs.append(os.path.join("include", "Primitives", "interface"))
        self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Basic", "interface"))
        if self.settings.os == "Android":
            self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Android", "interface"))
        elif is_apple_os(self):
            self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Apple", "interface"))
        elif self.settings.os == "Emscripten":
            self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Emscripten", "interface"))
        elif self.settings.os == "Linux":
            self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Linux", "interface"))
        elif self.settings.os == "Windows":
            self.cpp_info.includedirs.append(os.path.join("include", "Platforms", "Win32", "interface"))
            self.cpp_info.includedirs.append(os.path.join("include", "Graphics", "GraphicsEngineD3D11", "interface"))
            self.cpp_info.includedirs.append(os.path.join("include", "Graphics", "GraphicsEngineD3D12", "interface"))

        self.cpp_info.defines.append(f"DILIGENT_SPIRV_CROSS_NAMESPACE={self.dependencies['spirv-cross'].options.namespace}")
        self.cpp_info.defines.append(f"{self._diligent_platform}=1")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "pthread"]
        elif self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa", "AppKit"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["dxgi", "shlwapi"]
        elif self.settings.os == "Android":
            self.cpp_info.system_libs = ["android", "log"]
