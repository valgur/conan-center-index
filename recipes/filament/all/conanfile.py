import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class FilamentConan(ConanFile):
    name = "filament"
    description = "Filament is a real-time physically based rendering engine for Android, iOS, Windows, Linux, macOS, and WebGL2"
    license = "Apache-2.0"
    homepage = "https://google.github.io/filament/"
    topics = ("3d-graphics", "android", "webgl", "real-time", "opengl", "metal", "graphics", "vulkan", "wasm", "opengl-es", "pbr", "gltf", "gltf-viewer")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # Feature options
        "enable_lto": [True, False],
        "enable_multiview": [True, False],
        "enable_feature_level_0": [True, False],
        "enable_fgviewer": [True, False],
        "enable_matdbg": [True, False],
        "enable_matopt": [True, False],
        "build_filamat": [True, False],
        "linux_is_mobile": [True, False],
        # Graphics backend support
        "with_opengl": [True, False],
        "with_vulkan": [True, False],
        "with_metal": [True, False],
        "with_webgpu": [True, False],
        # Platform-specific options
        "with_gles3": [True, False],
        "with_xcb": [True, False],
        "with_xlib": [True, False],
        "with_wayland": [True, False],
        "with_egl": [True, False],
        "with_sdl2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_lto": False,
        "enable_multiview": False,
        "enable_feature_level_0": True,
        "enable_fgviewer": False,
        "enable_matdbg": False,
        "enable_matopt": False,
        "build_filamat": True,
        "linux_is_mobile": False,
        "with_egl": False,
        "with_gles3": False,
        "with_metal": True,
        "with_opengl": True,
        "with_sdl2": False,
        "with_vulkan": True,
        "with_wayland": False,
        "with_webgpu": False,
        "with_xcb": True,
        "with_xlib": True,

        "tinyexr/*:header_only": False,
        "glslang/*:install_internal_headers": True,
        "glslang/*:shared": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not is_apple_os(self):
            del self.options.with_metal
        if self.settings.os != "Linux":
            del self.options.with_egl
            del self.options.with_wayland
            del self.options.with_xcb
            del self.options.with_xlib
            del self.options.linux_is_mobile

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        if self.options.get_safe("with_egl"):
            self.requires("egl/system")
        if self.options.get_safe("with_wayland"):
            self.requires("wayland/[^1.22.0]")
        if self.options.get_safe("with_xlib") or self.options.get_safe("with_xcb"):
            self.requires("xorg/system")

        self.requires("abseil/[>=20230125]", transitive_headers=True)
        self.requires("libbasisu/[^1.16 <1.50]")
        self.requires("civetweb/[^1.15]")
        # 1.91.5 and newer are not compatible due to https://github.com/ocornut/imgui/commit/191a728ecca454f11ff473e285804d1f7362a83d
        self.requires("imgui/[<1.91.5]")
        self.requires("tsl-robin-map/[^1.2]")
        self.requires("smol-v/[*]")
        self.requires("benchmark/[^1.8]")
        self.requires("meshoptimizer/[>=0.20 <1]")
        self.requires("mikktspace/[*]")
        self.requires("cgltf/[^1.13]")
        self.requires("draco/[^1.5]")
        self.requires("jsmn/[^1.1]")
        self.requires("stb/[*]")
        self.requires("perfetto/[*]")
        self.requires("zstd/[^1.5]")

        # Host platform dependencies
        if not self._is_mobile_target:
            self.requires("assimp/[^5.3]")
            self.requires("libpng/[^1.6]")
            if self.options.with_sdl2:
                self.requires("sdl/[^2.28]")
            self.requires("zlib-ng/[^2.0]")
            self.requires("tinyexr/[^1.0]")

        # SPIRV tools for filamat
        if self.options.build_filamat:
            self.requires("glslang/[^1.4.321.0]")
            self.requires("spirv-tools/[^1.4.321.0]")
            self.requires("spirv-cross/[^1.4.321.0]")

        # Vulkan dependencies
        if self.options.with_vulkan:
            self.requires("vulkan-memory-allocator/[^3.0]")
            self.requires("spirv-headers/[^1.4.321.0]")

        # WebGPU dependencies
        if self.options.with_webgpu:
            self.requires("dawn/[^1.0]")

    def validate(self):
        check_min_cppstd(self, 20)
        if self.settings.compiler not in ["clang", "apple-clang", "msvc"]:
            raise ConanInvalidConfiguration("Filament only supports Clang and MSVC compilers")
        # Backend validation
        if self.settings.os == "Windows" and self.options.with_vulkan == False and self.options.with_opengl == False:
            raise ConanInvalidConfiguration("At least one graphics backend must be enabled")
        if is_apple_os(self) and not self.options.with_metal and not self.options.with_opengl:
            raise ConanInvalidConfiguration("Metal or OpenGL backend required on macOS")
        if self.options.build_filamat and self.dependencies["glslang"].options.shared:
            raise ConanInvalidConfiguration("glslang can only be used as a static library")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.19]")

    @property
    def _is_mobile_target(self):
        return self.settings.os in ["Android", "iOS"] or self.options.linux_is_mobile

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)

        # Disable tests, samples, benchmarks
        tc.cache_variables["FILAMENT_SKIP_SAMPLES"] = True
        tc.cache_variables["BUILD_TESTING"] = False

        # Core options mapping
        tc.cache_variables["FILAMENT_USE_EXTERNAL_GLES3"] = self.options.with_gles3
        tc.cache_variables["FILAMENT_ENABLE_LTO"] = self.options.enable_lto
        tc.cache_variables["FILAMENT_SUPPORTS_XCB"] = self.options.get_safe("with_xcb")
        tc.cache_variables["FILAMENT_SUPPORTS_XLIB"] = self.options.get_safe("with_xlib")
        tc.cache_variables["FILAMENT_SUPPORTS_EGL_ON_LINUX"] = self.options.get_safe("with_egl")
        tc.cache_variables["FILAMENT_SUPPORTS_WAYLAND"] = self.options.get_safe("with_wayland")
        tc.cache_variables["FILAMENT_SKIP_SDL2"] = not self.options.with_sdl2
        tc.cache_variables["FILAMENT_LINUX_IS_MOBILE"] = self.options.get_safe("linux_is_mobile")
        tc.cache_variables["FILAMENT_ENABLE_FEATURE_LEVEL_0"] = self.options.enable_feature_level_0
        tc.cache_variables["FILAMENT_ENABLE_MULTIVIEW"] = self.options.enable_multiview
        tc.cache_variables["FILAMENT_SUPPORTS_OSMESA"] = False
        tc.cache_variables["FILAMENT_ENABLE_FGVIEWER"] = self.options.enable_fgviewer

        # Backend support
        tc.cache_variables["FILAMENT_SUPPORTS_OPENGL"] = self.options.with_opengl
        tc.cache_variables["FILAMENT_SUPPORTS_VULKAN"] = self.options.with_vulkan
        tc.cache_variables["FILAMENT_SUPPORTS_METAL"] = self.options.get_safe("with_metal")
        tc.cache_variables["FILAMENT_SUPPORTS_WEBGPU"] = self.options.with_webgpu

        # Feature options
        tc.cache_variables["FILAMENT_BUILD_FILAMAT"] = self.options.build_filamat
        tc.cache_variables["FILAMENT_ENABLE_MATDBG"] = self.options.enable_matdbg
        tc.cache_variables["FILAMENT_DISABLE_MATOPT"] = not self.options.enable_matopt

        tc.cache_variables["USE_STATIC_LIBCXX"] = False
        tc.cache_variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)

        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("cgltf", "cmake_target_name", "cgltf")
        deps.set_property("draco", "cmake_target_name", "dracodec")
        deps.set_property("civetweb", "cmake_target_name", "civetweb")
        deps.set_property("glslang", "cmake_target_name", "glslang")
        deps.set_property("imgui", "cmake_target_name", "imgui")
        deps.set_property("jsmn", "cmake_target_name", "jsmn")
        deps.set_property("libbasisu", "cmake_target_aliases", ["basis_encoder", "basis_transcoder"])
        deps.set_property("libpng", "cmake_target_name", "png::png")
        deps.set_property("meshoptimizer", "cmake_target_name", "meshoptimizer")
        deps.set_property("mikktspace", "cmake_target_name", "mikktspace")
        deps.set_property("smol-v", "cmake_target_name", "smol-v")
        deps.set_property("stb", "cmake_target_name", "stb")
        deps.set_property("tinyexr", "cmake_target_name", "tinyexr")
        deps.set_property("zlib-ng", "cmake_target_name", "z")
        deps.set_property("zstd", "cmake_target_name", "zstd")
        deps.set_property("spirv-headers", "cmake_target_name", "SPIRV-Headers")
        deps.set_property("spirv-tools", "cmake_target_name", "spirv-tools")
        deps.set_property("spirv-cross", "cmake_target_name", "spirv-cross")
        deps.set_property("spirv-tools::spirv-tools-core", "cmake_target_name", "SPIRV-Tools")
        deps.set_property("spirv-tools::spirv-tools-opt", "cmake_target_name", "SPIRV-Tools-opt")
        deps.set_property("spirv-cross::spirv-cross-core", "cmake_target_name", "spirv-cross-core")
        deps.set_property("spirv-cross::spirv-cross-glsl", "cmake_target_name", "spirv-cross-glsl")
        deps.set_property("vulkan-memory-allocator", "cmake_target_name", "vkmemalloc")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        # Main filament library
        self.cpp_info.components["filament"].set_property("cmake_target_name", "filament::filament")
        self.cpp_info.components["filament"].libs = ["filament"]
        self.cpp_info.components["filament"].requires = ["utils", "filabridge", "filaflat", "backend"]

        # Core libraries
        self.cpp_info.components["utils"].libs = ["utils"]
        self.cpp_info.components["utils"].requires = ["tsl"]

        # Backend library
        self.cpp_info.components["backend"].set_property("cmake_target_name", "filament::backend")
        self.cpp_info.components["backend"].libs = ["backend"]
        self.cpp_info.components["backend"].requires = ["utils", "abseil::abseil"]

        # Bridge library
        self.cpp_info.components["filabridge"].set_property("cmake_target_name", "filament::filabridge")
        self.cpp_info.components["filabridge"].libs = ["filabridge"]
        self.cpp_info.components["filabridge"].requires = ["utils"]

        # Flat library
        self.cpp_info.components["filaflat"].set_property("cmake_target_name", "filament::filaflat")
        self.cpp_info.components["filaflat"].libs = ["filaflat"]
        self.cpp_info.components["filaflat"].requires = ["utils", "filabridge"]

        # Math library
        self.cpp_info.components["math"].set_property("cmake_target_name", "filament::math")
        self.cpp_info.components["math"].libs = ["math"]

        # TSL (robin-map wrapper)
        self.cpp_info.components["tsl"].set_property("cmake_target_name", "filament::tsl")
        self.cpp_info.components["tsl"].requires = ["robin-map::robin-map"]

        # Optional components based on build options
        if self.options.build_filamat:
            self.cpp_info.components["filamat"].set_property("cmake_target_name", "filament::filamat")
            self.cpp_info.components["filamat"].libs = ["filamat", "shaders", "smol-v"]
            self.cpp_info.components["filamat"].requires = ["utils", "filabridge", "spirv-tools::spirv-tools",
                                                            "glslang::glslang", "spirv-cross::spirv-cross"]

        # Geometry library
        self.cpp_info.components["geometry"].set_property("cmake_target_name", "filament::geometry")
        self.cpp_info.components["geometry"].libs = ["geometry"]
        self.cpp_info.components["geometry"].requires = ["math", "utils", "meshoptimizer::meshoptimizer", "mikktspace::mikktspace"]

        # Image library
        self.cpp_info.components["image"].set_property("cmake_target_name", "filament::image")
        self.cpp_info.components["image"].libs = ["image"]
        self.cpp_info.components["image"].requires = ["math", "utils"]

        # IBL library
        self.cpp_info.components["ibl"].set_property("cmake_target_name", "filament::ibl")
        self.cpp_info.components["ibl"].libs = ["ibl"]
        self.cpp_info.components["ibl"].requires = ["filament", "image", "utils", "math"]

        # Camera utilities
        self.cpp_info.components["camutils"].set_property("cmake_target_name", "filament::camutils")
        self.cpp_info.components["camutils"].libs = ["camutils"]
        self.cpp_info.components["camutils"].requires = ["math"]

        # glTF I/O
        self.cpp_info.components["gltfio_core"].set_property("cmake_target_name", "filament::gltfio_core")
        self.cpp_info.components["gltfio_core"].libs = ["gltfio_core", "dracodec", "uberarchive"]
        self.cpp_info.components["gltfio_core"].requires = ["filament", "geometry", "cgltf::cgltf", "draco::draco", "stb::stb"]

        # Mesh I/O
        self.cpp_info.components["filameshio"].set_property("cmake_target_name", "filament::filameshio")
        self.cpp_info.components["filameshio"].libs = ["filameshio"]
        self.cpp_info.components["filameshio"].requires = ["filament", "meshoptimizer::meshoptimizer"]

        # KTX reader
        self.cpp_info.components["ktxreader"].set_property("cmake_target_name", "filament::ktxreader")
        self.cpp_info.components["ktxreader"].libs = ["ktxreader", "basis_transcoder"]
        self.cpp_info.components["ktxreader"].requires = ["image", "filament", "libbasisu::libbasisu"]

        # Viewer library (if not mobile)
        if not self._is_mobile_target:
            self.cpp_info.components["viewer"].set_property("cmake_target_name", "filament::viewer")
            self.cpp_info.components["viewer"].libs = ["viewer"]
            self.cpp_info.components["viewer"].requires = ["filament", "gltfio_core", "camutils", "civetweb::civetweb"]
            if self.options.with_sdl2:
                self.cpp_info.components["viewer"].requires.append("sdl::sdl")

        # Platform-specific system libraries
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["backend"].system_libs = ["dl"]
            self.cpp_info.components["utils"].system_libs = ["pthread"]
            if self.options.with_egl:
                self.cpp_info.components["backend"].system_libs.append("EGL")
        elif is_apple_os(self):
            if self.options.with_metal:
                self.cpp_info.components["backend"].frameworks = ["Metal", "CoreVideo"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["utils"].system_libs = ["ws2_32"]

        # Vulkan-specific components
        if self.options.with_vulkan:
            self.cpp_info.components["bluevk"].set_property("cmake_target_name", "filament::bluevk")
            self.cpp_info.components["bluevk"].libs = ["bluevk"]
            self.cpp_info.components["bluevk"].requires = ["vulkan-memory-allocator::vulkan-memory-allocator", "spirv-headers::spirv-headers"]
            self.cpp_info.components["backend"].requires.append("bluevk")

        # WebGPU-specific components
        if self.options.with_webgpu:
            self.cpp_info.components["backend"].requires.append("dawn::dawn")
