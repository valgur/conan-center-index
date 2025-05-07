import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MoltenVKConan(ConanFile):
    name = "moltenvk"
    description = "MoltenVK is a Vulkan Portability implementation. It " \
                  "layers a subset of the high-performance, industry-standard " \
                  "Vulkan graphics and compute API over Apple's Metal " \
                  "graphics framework, enabling Vulkan applications to run " \
                  "on iOS and macOS."
    license = "Apache-2.0"
    topics = ("moltenvk", "khronos", "vulkan", "metal")
    homepage = "https://github.com/KhronosGroup/MoltenVK"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "hide_vulkan_symbols": [True, False],
        "with_spirv_tools": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "hide_vulkan_symbols": False,
        "with_spirv_tools": True,
        "tools": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        else:
            self.options.rm_safe("hide_vulkan_symbols")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cereal/[^1.3.2]")
        vulkan_version = self.conan_data["vulkan_version"][self.version]
        self.requires(f"glslang/{vulkan_version}")
        self.requires(f"spirv-cross/{vulkan_version}")
        self.requires(f"vulkan-headers/{vulkan_version}", transitive_headers=True)
        if self.options.with_spirv_tools:
            self.requires(f"spirv-tools/{vulkan_version}")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.os not in ["Macos", "iOS", "tvOS"]:
            raise ConanInvalidConfiguration(f"{self.ref} only supported on MacOS, iOS and tvOS")
        if self.settings.compiler != "apple-clang":
            raise ConanInvalidConfiguration(f"{self.ref} requires apple-clang")
        if Version(self.settings.compiler.version) < "12.0":
            raise ConanInvalidConfiguration(f"{self.ref} requires XCode 12.0 or higher")
        spirv_cross = self.dependencies["spirv-cross"]
        if spirv_cross.options.shared or not (spirv_cross.options.msl and spirv_cross.options.reflect):
            raise ConanInvalidConfiguration(f"{self.ref} requires spirv-cross static with msl & reflect enabled")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MVK_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["MVK_VERSION"] = self.version
        tc.variables["MVK_WITH_SPIRV_TOOLS"] = self.options.with_spirv_tools
        tc.variables["MVK_BUILD_SHADERCONVERTER_TOOL"] = self.options.tools
        if self.options.shared:
            tc.variables["MVK_HIDE_VULKAN_SYMBOLS"] = self.options.hide_vulkan_symbols
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["MoltenVK"]
        self.cpp_info.frameworks = ["Metal", "Foundation", "CoreFoundation", "QuartzCore", "IOSurface", "CoreGraphics"]
        if self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["AppKit", "IOKit"])
        elif self.settings.os in ["iOS", "tvOS"]:
            self.cpp_info.frameworks.append("UIKit")

        self.cpp_info.requires = [
            "cereal::cereal", "glslang::glslang-core", "glslang::spirv", "spirv-cross::spirv-cross-core",
            "spirv-cross::spirv-cross-msl", "spirv-cross::spirv-cross-reflect", "vulkan-headers::vulkan-headers",
        ]
        if self.options.with_spirv_tools:
            self.cpp_info.requires.append("spirv-tools::spirv-tools-core")

        if self.options.shared:
            moltenvk_icd_path = os.path.join(self.package_folder, "lib", "MoltenVK_icd.json")
            self.runenv_info.prepend_path("VK_DRIVER_FILES", moltenvk_icd_path)
            self.runenv_info.prepend_path("VK_ICD_FILENAMES", moltenvk_icd_path)
