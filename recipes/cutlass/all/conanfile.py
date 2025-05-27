import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CutlassConan(ConanFile):
    name = "cutlass"
    description = "CUTLASS: CUDA Templates for Linear Algebra Subroutines"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/NVIDIA/cutlass"
    topics = ("linear-algebra", "gpu", "cuda", "deep-learning", "nvidia", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    # TODO: add header_only=False option

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.19 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Don't look for CUDA, we're only installing the headers
        replace_in_file(self, "CMakeLists.txt",
                        "include(${CMAKE_CURRENT_SOURCE_DIR}/CUDA.cmake)",
                        textwrap.dedent("""
                            if(NOT CUTLASS_ENABLE_HEADERS_ONLY)
                                include(${CMAKE_CURRENT_SOURCE_DIR}/CUDA.cmake)
                            endif()
                        """))

    def generate(self):
        # Install via CMake to ensure headers are configured correctly
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_SUPPRESS_REGENERATION"] = True
        tc.cache_variables["CUTLASS_REVISION"]=f"v{self.version}"
        tc.cache_variables["CUTLASS_NATIVE_CUDA"] = False
        tc.cache_variables["CUTLASS_ENABLE_HEADERS_ONLY"] = True
        tc.cache_variables["CUTLASS_ENABLE_TOOLS"] = False
        tc.cache_variables["CUTLASS_ENABLE_LIBRARY"] = False
        tc.cache_variables["CUTLASS_ENABLE_PROFILER"] = False
        tc.cache_variables["CUTLASS_ENABLE_PERFORMANCE"] = False
        tc.cache_variables["CUTLASS_ENABLE_TESTS"] = False
        tc.cache_variables["CUTLASS_ENABLE_GTEST_UNIT_TESTS"] = False
        tc.cache_variables["CUTLASS_ENABLE_CUBLAS"] = False
        tc.cache_variables["CUTLASS_ENABLE_CUDNN"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "test"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "NvidiaCutlass")
        self.cpp_info.set_property("cmake_target_name", "nvidia::cutlass::cutlass")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
