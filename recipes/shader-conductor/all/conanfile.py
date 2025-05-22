import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ShaderConductorConan(ConanFile):
    name = "shader-conductor"
    description = "ShaderConductor is a tool designed for cross-compiling HLSL to other shading languages"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/ShaderConductor"
    topics = ("hlsl", "shader", "cross-compiler", "glsl", "essl", "msl")
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

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cxxopts/[^3.0]")
        self.requires("directx-shader-compiler/[^1.8.2502]", options={"install_internal_libs": True})
        self.requires("spirv-cross/[^1.3.239.0]", options={"shared": False})
        self.requires("spirv-headers/[^1.3.239.0]")
        self.requires("spirv-tools/[^1.3.239.0]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.dependencies["spirv-cross"].options.shared:
            raise ConanInvalidConfiguration("spirv-cross must be built as a static library")

    def build_requirements(self):
        # TODO: clang-format
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

        replace_in_file(self, "CMakeLists.txt", "-std=c++1z", "")
        replace_in_file(self, "Source/CMakeLists.txt", "/std:c++17", "")
        replace_in_file(self, "Source/CMakeLists.txt", "/std:c++14", "")
        replace_in_file(self, "Source/CMakeLists.txt", "-Werror", "")
        replace_in_file(self, "Source/CMakeLists.txt", "/WX", "")
        save(self, "Source/Tests/CMakeLists.txt", "")
        save(self, "External/CMakeLists.txt", "")
        replace_in_file(self, "Source/Core/CMakeLists.txt", "add_custom_target(CopyDxcompiler ALL", "add_custom_target(CopyDxcompiler ")
        replace_in_file(self, "Source/Core/CMakeLists.txt", "add_dependencies(${LIB_NAME} CopyDxcompiler)", "")

        path = Path("Include/ShaderConductor/ShaderConductor.hpp")
        path.write_text("#include <cstdint>\n" + path.read_text())

        replace_in_file(self, "Source/Core/ShaderConductor.cpp",
                        "dxc/Support/WinAdapter.h>",
                        "dxc/WinAdapter.h>")
        replace_in_file(self, "Source/Core/ShaderConductor.cpp",
                        "Unicode::UTF16ToUTF8String",
                        "Unicode::WideToUTF8String")
        replace_in_file(self, "Source/Core/ShaderConductor.cpp",
                        "Unicode::UTF8ToUTF16String",
                        "Unicode::UTF8ToWideString")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_ShaderConductor_INCLUDE"] = "conan_deps.cmake"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        if self.settings.arch not in ["x86", "x86_64"]:
            replace_in_file(self, "Source/CMakeLists.txt", "-msse2", "")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "Lib"), os.path.join(self.package_folder, "lib"))
        copy(self, "*", os.path.join(self.build_folder, "Bin"), os.path.join(self.package_folder, "bin"))
        copy(self, "*", os.path.join(self.source_folder, "Include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        # Unofficial CMake name and targets
        self.cpp_info.set_property("cmake_file_name", "ShaderConductor")
        self.cpp_info.set_property("cmake_target_name", "ShaderConductor")
        self.cpp_info.set_property("cmake_target_aliases", ["ShaderConductor::ShaderConductor"])
        self.cpp_info.libs = ["ShaderConductor"]
        self.cpp_info.includedirs.append(os.path.join("include", "ShaderConductor"))
