import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class VkBootstrapConan(ConanFile):
    name = "vk-bootstrap"
    description = "Vulkan bootstrapping library."
    license = "MIT"
    topics = ("vulkan", "bootstrap", "setup")
    homepage = "https://github.com/charles-lunarg/vk-bootstrap"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _min_cppstd(self):
        if Version(self.version) >= "1.3.270":
            return 17
        return 14

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _headers_version(self):
        return {}.get(self.version, f"{self.version}.0")

    def requirements(self):
        if Version(self.version) >= "1.0":
            self.requires(f"vulkan-headers/{self._headers_version}", transitive_headers=True)
        else:
            self.requires("vulkan-headers/1.4.309.0", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported with Visual Studio")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        if Version(self.version) >= "1.0":
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                            "add_library(vk-bootstrap STATIC ", "add_library(vk-bootstrap ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["VK_BOOTSTRAP_TEST"] = False
        tc.variables["VK_BOOTSTRAP_WERROR"] = False
        if Version(self.version) < "1.0":
            vulkan_headers = self.dependencies["vulkan-headers"]
            includedirs = ";".join(
                os.path.join(vulkan_headers.package_folder, includedir).replace("\\", "/")
                for includedir in vulkan_headers.cpp_info.includedirs
            )
            tc.variables["VK_BOOTSTRAP_VULKAN_HEADER_DIR"] = includedirs
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = ["vk-bootstrap"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl"]
