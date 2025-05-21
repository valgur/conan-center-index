import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class DirectXShaderCompilerConan(ConanFile):
    name = "directx-shader-compiler"
    description = ("The DirectX Shader Compiler project includes a compiler and related tools used to compile "
                   "High-Level Shader Language (HLSL) programs into DirectX Intermediate Language (DXIL) representation.")
    license = "Apache-2.0 WITH LLVM-exception"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    topics = ("directx", "shader", "compiler", "hlsl", "dxil")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("miniz/[>=2.1.0 <4]")
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("spirv-headers/[~1.4.309.0]")
        self.requires("spirv-tools/[~1.4.309.0]")
        # Newer versions have a conflict in wsl/stubs/basetsd.h
        self.requires("directx-headers/[<1.603]", libs=False)

    def validate(self):
        if not self.settings.os in ["Linux", "Windows"]:
            raise ConanInvalidConfiguration(f"{self.name} is not supported on {self.settings.os}")
        check_min_cppstd(self, 17)

    def build_requirements(self):
        # <4 is required to support CMP0051=OLD
        self.tool_requires("cmake/[>=3.17.2 <4]")
        # TODO: clang-format

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

        replace_in_file(self, "CMakeLists.txt",
                        "set(CMAKE_CXX_STANDARD 17)", "")

        replace_in_file(self, "lib/Support/CMakeLists.txt",
                        "set(system_libs ${system_libs} z)",
                        "find_package(ZLIB REQUIRED)\n"
                        "set(system_libs ${system_libs} ZLIB::ZLIB)")

        replace_in_file(self, "external/CMakeLists.txt",
                        'message(FATAL_ERROR "SPIRV-Tools was not found',
                        "find_package(SPIRV-Tools REQUIRED) #")
        replace_in_file(self, "external/CMakeLists.txt",
                        'set_property(TARGET ${target} PROPERTY FOLDER', "#")

        path = Path("tools/clang/lib/SPIRV/CMakeLists.txt")
        path.write_text("find_package(SPIRV-Tools REQUIRED)\n\n" + path.read_text())

        rm(self, "miniz.*", "lib/DxilCompression")
        rmdir(self, "include/miniz")

    def generate(self):
        tc = CMakeToolchain(self)

        # Shared by default, setting BUILD_SHARED_LIBS=True only breaks things
        tc.cache_variables["BUILD_SHARED_LIBS"] = False

        # https://github.com/microsoft/DirectXShaderCompiler/blob/v1.8.2502/cmake/caches/PredefinedParams.cmake
        tc.cache_variables["CMAKE_EXPORT_COMPILE_COMMANDS"] = True
        tc.cache_variables["LLVM_APPEND_VC_REV"] = True
        tc.cache_variables["LLVM_DEFAULT_TARGET_TRIPLE"] = "dxil-ms-dx"
        tc.cache_variables["LLVM_ENABLE_EH"] = True
        tc.cache_variables["LLVM_ENABLE_RTTI"] = True
        tc.cache_variables["LLVM_INCLUDE_DOCS"] = False
        tc.cache_variables["LLVM_INCLUDE_EXAMPLES"] = False
        tc.cache_variables["LLVM_OPTIMIZED_TABLEGEN"] = False
        tc.cache_variables["LLVM_TARGETS_TO_BUILD"] = "None"
        tc.cache_variables["LIBCLANG_BUILD_STATIC"] = True
        tc.cache_variables["CLANG_BUILD_EXAMPLES"] = False
        tc.cache_variables["CLANG_CL"] = False
        tc.cache_variables["CLANG_ENABLE_ARCMT"] = False
        tc.cache_variables["CLANG_ENABLE_STATIC_ANALYZER"] = False
        tc.cache_variables["ENABLE_SPIRV_CODEGEN"] = True
        tc.cache_variables["LLVM_ENABLE_TERMINFO"] = False

        tc.cache_variables["HLSL_INCLUDE_TESTS"] = False
        tc.cache_variables["HLSL_OFFICIAL_BUILD"] = True
        tc.cache_variables["HLSL_SUPPORT_QUERY_GIT_COMMIT_INFO"] = False
        tc.cache_variables["LLVM_BUILD_TOOLS"] = False
        tc.cache_variables["LLVM_ENABLE_LTO"] = False
        tc.cache_variables["LLVM_INCLUDE_TESTS"] = False
        tc.cache_variables["LLVM_INCLUDE_UTILS"] = False
        tc.cache_variables["LLVM_INSTALL_TOOLCHAIN_ONLY"] = False
        tc.cache_variables["SPIRV_BUILD_TESTS"] = False

        tc.cache_variables["LLVM_ENABLE_ZLIB"] = True
        tc.cache_variables["HAVE_LIBZ"] = True
        tc.cache_variables["HAVE_ZLIB_H"] = True

        tc.cache_variables["SPIRV-Headers_SOURCE_DIR"] = self.dependencies["spirv-headers"].package_folder.replace("\\", "/")
        tc.cache_variables["DXC_SPIRV_TOOLS_DIR"] = ""
        tc.cache_variables["SPIRV_TOOLS_INCLUDE_DIR"] = self.dependencies["spirv-tools"].cpp_info.includedir.replace("\\", "/")
        tc.cache_variables["DIRECTX_HEADER_INCLUDE_DIR"] = os.path.join(self.dependencies["directx-headers"].package_folder, "include").replace("\\", "/")
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
        rm(self, "llvm-*", os.path.join(self.package_folder, "bin"))
        rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        for subdir in ["clang", "clang-c", "llvm", "llvm-c"]:
            rmdir(self, os.path.join(self.package_folder, "include", subdir))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        # No official CMake config is exported.
        # Match https://github.com/microsoft/vcpkg/blob/master/ports/directx-dxc/directx-dxc-config.cmake.in instead

        self.cpp_info.set_property("cmake_file_name", "DirectXShaderCompiler")

        self.cpp_info.components["dxcompiler"].set_property("cmake_target_name", "dxcompiler")
        self.cpp_info.components["dxcompiler"].set_property("cmake_target_aliases", ["Microsoft::DirectXShaderCompiler"])
        self.cpp_info.components["dxcompiler"].libs = ["dxcompiler"]
        self.cpp_info.components["dxcompiler"].requires = [
            "dxil",
            "zlib::zlib",
            "spirv-headers::spirv-headers",
            "spirv-tools::spirv-tools-core",
            "spirv-tools::spirv-tools-opt",
            "directx-headers::directx-headers",
        ]

        self.cpp_info.components["dxil"].set_property("cmake_target_name", "dxil")
        self.cpp_info.components["dxil"].set_property("cmake_target_aliases", ["Microsoft::DXIL"])
        self.cpp_info.components["dxil"].libs = ["dxil"]
        self.cpp_info.components["dxil"].requires = [
            "zlib::zlib",
            "miniz::miniz",
            "directx-headers::directx-headers",
        ]
