import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class VulkanHeadersConan(ConanFile):
    name = "vulkan-headers"
    description = "Vulkan Header files."
    license = "Apache-2.0"
    topics = ("vulkan-headers", "vulkan")
    homepage = "https://github.com/KhronosGroup/Vulkan-Headers"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    package_id_embed_mode = "patch_mode"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    options = {
        "module": [True, False],
        "module_std": [True, False],
    }
    default_options = {
        "module": False,
        "module_std": False,
    }
    options_description = {
        "module": "Enables building of the Vulkan C++20 module",
        "module_std": "Enables building of the Vulkan C++20 module with import std",
    }

    def config_options(self):
        if Version(self.version) < "1.3.289":
            del self.options.module
        if Version(self.version) < "1.4.311":
            del self.options.module_std

    def configure(self):
        if not self.options.get_safe("module"):
            self.options.rm_safe("module_std")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.options.get_safe("module"):
            check_min_cppstd(self, 20)
        if self.options.get_safe("module_std"):
            check_min_cppstd(self, 23)

    def validate_build(self):
        if self.options.get_safe("module"):
            compiler_version = Version(self.settings.compiler.version)
            if self.settings.compiler == "msvc" and compiler_version < "194":
                raise ConanInvalidConfiguration("Module support requires MSVC 19.41 or higher")
            if self.settings.compiler == "clang" and compiler_version < "16":
                raise ConanInvalidConfiguration("Module support requires Clang 16.0 or higher")
            if self.settings.compiler == "gcc" and compiler_version < "14":
                raise ConanInvalidConfiguration("Module support requires GCC 14.0 or higher")

    def build_requirements(self):
        if self.options.get_safe("module"):
            self.tool_requires("cmake/[>=3.30 <5]")
            self.tool_requires("ninja/[^1.10]")
        elif Version(self.version) >= "1.4.309.0":
            self.tool_requires("cmake/[>=3.22.1 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja" if self.options.get_safe("module") else None)
        tc.cache_variables["VULKAN_HEADERS_ENABLE_TESTS"] = False
        tc.cache_variables["VULKAN_HEADERS_ENABLE_MODULE"] = self.options.get_safe("module", False)
        tc.cache_variables["VULKAN_HEADERS_ENABLE_MODULE_STD"] = self.options.get_safe("module_std", False)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "share", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "VulkanHeaders")

        # The version in the official CMake ConfigVersion.cmake has only three components: major.minor.patch
        # Vulkan interprets four-part version strings as variant.major.minor.patch, which
        # can unintentionally invalidate compatibility checks in consuming code.
        # https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html#extendingvulkan-coreversions-versionnumbers
        # https://github.com/KhronosGroup/Vulkan-Loader/blob/vulkan-sdk-1.4.313.0/loader/loader.c#L2499-L2507
        three_part_version = self.version.rsplit(".", 1)[0]
        self.cpp_info.set_property("system_package_version", three_part_version)

        self.cpp_info.components["vulkanheaders"].set_property("cmake_target_name", "Vulkan::Headers")
        self.cpp_info.components["vulkanheaders"].bindirs = []
        self.cpp_info.components["vulkanheaders"].libdirs = []

        self.cpp_info.components["vulkanregistry"].set_property("cmake_target_name", "Vulkan::Registry")
        self.cpp_info.components["vulkanregistry"].includedirs = [os.path.join("share", "vulkan", "registry")]
        self.cpp_info.components["vulkanregistry"].bindirs = []
        self.cpp_info.components["vulkanregistry"].libdirs = []
        self.cpp_info.components["vulkanregistry"].resdirs = ["share"]

        if self.options.get_safe("module"):
            #   target_sources(Vulkan::HppModule
            #     INTERFACE
            #       FILE_SET "module"
            #       TYPE "CXX_MODULES"
            #       BASE_DIRS "<package_folder>"
            #       FILES "<package_folder>/include/vulkan/vulkan.cppm"
            #   )
            self.cpp_info.components["module"].set_property("cmake_target_name", "Vulkan::HppModule")
            self.cpp_info.requres = ["vulkanheaders"]
