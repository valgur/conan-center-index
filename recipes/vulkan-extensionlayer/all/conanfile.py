import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.0"


class VulkanExtensionLayerConan(ConanFile):
    name = "vulkan-extensionlayer"
    description = "Layer providing Vulkan features when native support is unavailable"
    license = "Apache-2.0"
    homepage = "https://github.com/KhronosGroup/Vulkan-ExtensionLayer"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("vulkan", "gpu")
    package_type = "application"  # only exports dynamically-linked libraries
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"vulkan-utility-libraries/{self.version}", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22.0 <5]")
        # also requires Python 3.7+

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _manifests_dir(self):
        return

    def package(self):
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share"]
        # Look for dynamically-linked libraries here
        if self.settings.os != "Windows":
            self.cpp_info.bindirs = ["lib"]

        if self.settings.os == "Windows":
            manifest_dir = "bin"
        else:
            manifest_dir = os.path.join("share", "vulkan", "explicit_layer.d")
        self.runenv_info.append_path("VK_LAYER_PATH", os.path.join(self.package_folder, manifest_dir))

        three_part_version = self.version.rsplit(".", 1)[0]
        self.cpp_info.set_property("system_package_version", three_part_version)
