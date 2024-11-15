from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os

required_conan_version = ">=1.53.0"


class FilamentConan(ConanFile):
    name = "filament"
    description = "Filament is a real-time physically based rendering engine for Android, iOS, Windows, Linux, macOS, and WebGL2"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://google.github.io/filament/"
    topics = ("3d-graphics", "android", "webgl", "real-time", "opengl", "metal", "graphics", "vulkan", "wasm", "opengl-es", "pbr", "gltf", "gltf-viewer")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "opengl_support": [True, False],
        "vulkan_support": [True, False],
        "metal_support": [True, False],
        "egl_support": [True, False],
        "use_external_gles3": [True, False],
        "with_sdl2": [True, False],
        "with_wayland": [True, False],
        "with_xcb": [True, False],
        "with_xlib": [True, False],
        "feature_level_0": [True, False],
        "linux_is_mobile": [True, False],
        "lto": [True, False],
        "multiview": [True, False],
        "ndk_version": ["ANY"],
        "metal_handle_arena_size_in_mb": [None, "ANY"],
        "min_command_buffers_size_in_mb": [None, "ANY"],
        "opengl_handle_arena_size_in_mb": [None, "ANY"],
        "per_frame_commands_size_in_mb": [None, "ANY"],
        "per_render_pass_arena_size_in_mb": [None, "ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "opengl_support": True,
        "vulkan_support": True,
        "metal_support": True,
        "egl_support": True,
        "use_external_gles3": True,
        "with_sdl2": True,
        "with_wayland": True,
        "with_xcb": True,
        "with_xlib": True,
        "feature_level_0": True,
        "linux_is_mobile": False,
        "lto": False,
        "multiview": False,
        "ndk_version": "",
        "metal_handle_arena_size_in_mb": None,
        "min_command_buffers_size_in_mb": None,
        "opengl_handle_arena_size_in_mb": None,
        "per_frame_commands_size_in_mb": None,
        "per_render_pass_arena_size_in_mb": None,
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "clang": "6",
            "apple-clang": "10",
            "msvc": "191",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not is_apple_os(self):
            del self.options.metal_support
            del self.options.metal_handle_arena_size_in_mb
        if self.settings.os != "Linux":
            del self.options.egl_support
            del self.options.with_wayland
            del self.options.with_xcb
            del self.options.with_xlib
            del self.options.linux_is_mobile
        if self.settings.os != "Android":
            del self.options.ndk_version

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("egl_support"):
            self.requires("egl/system")
        if self.options.get_safe("with_wayland"):
            self.requires("wayland/1.22.0")
        if self.options.get_safe("with_xlib") or self.options.get_safe("with_xcb"):
            self.requires("xorg/system")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        if not is_msvc(self) or  self.settings.compiler not in ["clang", "apple-clang"]:
            raise ConanInvalidConfiguration("Filament only supports Clang and MSVC compilers")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.19 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CCACHE_PROGRAM"] = False
        tc.variables["FILAMENT_ENABLE_ASAN_UBSAN"] = False
        tc.variables["FILAMENT_ENABLE_FEATURE_LEVEL_0"] = self.options.feature_level_0
        tc.variables["FILAMENT_ENABLE_JAVA"] = False
        tc.variables["FILAMENT_ENABLE_LTO"] = self.options.lto
        tc.variables["FILAMENT_ENABLE_MULTIVIEW"] = self.options.multiview
        tc.variables["FILAMENT_ENABLE_TSAN"] = False
        tc.variables["FILAMENT_LINUX_IS_MOBILE"] = self.options.get_safe("linux_is_mobile", False)
        tc.variables["FILAMENT_NDK_VERSION"] = self.options.get_safe("ndk_version", "")
        tc.variables["FILAMENT_SKIP_SAMPLES"] = True
        tc.variables["FILAMENT_SKIP_SDL2"] = not self.options.with_sdl2
        tc.variables["FILAMENT_SUPPORTS_EGL_ON_LINUX"] = self.options.get_safe("egl_support", False)
        tc.variables["FILAMENT_SUPPORTS_METAL"] = self.options.get_safe("metal_support", False)
        tc.variables["FILAMENT_SUPPORTS_OPENGL"] = self.options.opengl_support
        tc.variables["FILAMENT_SUPPORTS_VULKAN"] = self.options.vulkan_support
        tc.variables["FILAMENT_SUPPORTS_WAYLAND"] = self.options.get_safe("with_wayland", False)
        tc.variables["FILAMENT_SUPPORTS_XCB"] = self.options.get_safe("with_xcb", False)
        tc.variables["FILAMENT_SUPPORTS_XLIB"] = self.options.get_safe("with_xlib", False)
        tc.variables["FILAMENT_USE_EXTERNAL_GLES3"] = self.options.use_external_gles3
        tc.variables["USE_STATIC_CRT"] = is_msvc_static_runtime(self)
        tc.variables["USE_STATIC_LIBCXX"] = False
        if self.options.get_safe("metal_handle_arena_size_in_mb") is not None:
            tc.variables["FILAMENT_METAL_HANDLE_ARENA_SIZE_IN_MB"] = self.options.metal_handle_arena_size_in_mb
        if self.options.min_command_buffers_size_in_mb.value is not None:
            tc.variables["FILAMENT_MIN_COMMAND_BUFFERS_SIZE_IN_MB"] = self.options.min_command_buffers_size_in_mb
        if self.options.opengl_handle_arena_size_in_mb.value is not None:
            tc.variables["FILAMENT_OPENGL_HANDLE_ARENA_SIZE_IN_MB"] = self.options.opengl_handle_arena_size_in_mb
        if self.options.per_frame_commands_size_in_mb.value is not None:
            tc.variables["FILAMENT_PER_FRAME_COMMANDS_SIZE_IN_MB"] = self.options.per_frame_commands_size_in_mb
        if self.options.per_render_pass_arena_size_in_mb.value is not None:
            tc.variables["FILAMENT_PER_RENDER_PASS_ARENA_SIZE_IN_MB"] = self.options.per_render_pass_arena_size_in_mb
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        VirtualBuildEnv(self).generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
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
        self.cpp_info.libs = ["package_lib"]

        # if package has an official FindPACKAGE.cmake listed in https://cmake.org/cmake/help/latest/manual/cmake-modules.7.html#find-modules
        # examples: bzip2, freetype, gdal, icu, libcurl, libjpeg, libpng, libtiff, openssl, sqlite3, zlib...
        self.cpp_info.set_property("cmake_module_file_name", "PACKAGE")
        self.cpp_info.set_property("cmake_module_target_name", "PACKAGE::PACKAGE")
        # if package provides a CMake config file (package-config.cmake or packageConfig.cmake, with package::package target, usually installed in <prefix>/lib/cmake/<package>/)
        self.cpp_info.set_property("cmake_file_name", "package")
        self.cpp_info.set_property("cmake_target_name", "package::package")
        # if package provides a pkgconfig file (package.pc, usually installed in <prefix>/lib/pkgconfig/)
        self.cpp_info.set_property("pkg_config_name", "package")

        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")

        # To export additional CMake variables, such as upper-case variables otherwise set by the project's *-config.cmake,
        # you can copy or save a .cmake file under <prefix>/lib/cmake/ with content like
        #     set(XYZ_VERSION ${${CMAKE_FIND_PACKAGE_NAME}_VERSION})
        #     set(XYZ_INCLUDE_DIRS ${${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS})
        #     ...
        # and set the following fields:
        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))
        cmake_module = os.path.join("lib", "cmake", "conan-official-variables.cmake")
        self.cpp_info.set_property("cmake_build_modules", [cmake_module])
