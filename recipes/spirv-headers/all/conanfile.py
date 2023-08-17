from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
import os

required_conan_version = ">=1.52.0"


class SpirvheadersConan(ConanFile):
    name = "spirv-headers"
    description = "Header files for the SPIRV instruction set."
    license = "MIT-KhronosGroup"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/KhronosGroup/SPIRV-Headers"
    topics = ("spirv", "spirv-v", "vulkan", "opengl", "opencl", "khronos", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SPIRV_HEADERS_SKIP_EXAMPLES"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SPIRV-Headers")
        self.cpp_info.set_property("cmake_target_name", "SPIRV-Headers::SPIRV-Headers")
        self.cpp_info.set_property("pkg_config_name", "SPIRV-Headers")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        # TODO: to remove in conan v2 once cmake_find_package* & pkg_config generators removed
        self.cpp_info.names["cmake_find_package"] = "SPIRV-Headers"
        self.cpp_info.names["cmake_find_package_multi"] = "SPIRV-Headers"
