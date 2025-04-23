import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class SpirvLlvmTranslatorConan(ConanFile):
    name = "spirv-llvm-translator"
    description = "A tool and a library for bi-directional translation between SPIR-V and LLVM IR"
    license = "NCSA"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/KhronosGroup/SPIRV-LLVM-Translator"
    topics = ("spirv", "llvm", "llvm-ir")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_spirv_tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_spirv_tools": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("llvm-core/20.1.3")
        self.requires("spirv-headers/1.4.309.0")
        if self.options.with_spirv_tools:
            self.requires("spirv-tools/1.4.309.0")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[^4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # SPIRV-Tools-tools is not exposed as a separate package by Conan
        replace_in_file(self, "CMakeLists.txt", "find_package(SPIRV-Tools-tools)", "")
        # Not available in the Conan package, included automatically
        replace_in_file(self, "CMakeLists.txt", "include(LLVM-Config)", "")
        replace_in_file(self, "CMakeLists.txt",
                        "get_target_property(SPIRV_TOOLS_INCLUDE_DIRS ${SPIRV-Tools-library} INTERFACE_INCLUDE_DIRECTORIES)",
                        "set(SPIRV_TOOLS_INCLUDE_DIRS ${SPIRV-Tools_INCLUDE_DIRS})")
        # Compilation with the experimental LLVM SPIRV target fails, force-disable for now
        replace_in_file(self, "CMakeLists.txt", "if(spirv_present_result)", "if(FALSE)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LLVM_EXTERNAL_SPIRV_HEADERS_SOURCE_DIR"] = self.dependencies["spirv-headers"].package_folder.replace("\\", "/")
        tc.cache_variables["LLVM_SPIRV_ENABLE_LIBSPIRV_DIS"] = self.options.with_spirv_tools
        if self.options.with_spirv_tools:
            tc.cache_variables["SPIRV-Tools-tools_FOUND"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.TXT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "LLVMSPIRVLib")
        self.cpp_info.libs = ["LLVMSPIRVLib"]
