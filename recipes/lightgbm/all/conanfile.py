import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LightGBMConan(ConanFile):
    name = "lightgbm"
    description = (
        "A fast, distributed, high performance gradient boosting "
        "(GBT, GBDT, GBRT, GBM or MART) framework based on decision tree algorithms, "
        "used for ranking, classification and many other machine learning tasks."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/LightGBM"
    topics = ("machine-learning", "boosting")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cuda": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cuda": False,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0")
        self.requires("fast_double_parser/[>=0.7.0 <1]", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/[>=5]", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("with_openmp"):
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_cuda:
            self.cuda.requires("cudart")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.with_cuda:
            self.cuda.validate_settings()
            if not self.options.with_openmp:
                raise ConanInvalidConfiguration("-o with_cuda=True requires -o with_openmp=True")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        if Version(self.version) < "4.0":
            # For CMake v4 support
            replace_in_file(self, "CMakeLists.txt",
                            "cmake_minimum_required(VERSION ",
                            "cmake_minimum_required(VERSION 3.18) # ")
        # Fix vendored dependency includes
        if Version(self.version) < "4.6.0":
            for lib in ["fmt", "fast_double_parser"]:
                replace_in_file(self, "include/LightGBM/utils/common.h", f"../../../external_libs/{lib}/include/", "")
        # Unvendor Eigen3
        replace_in_file(self, "CMakeLists.txt", "include_directories(${EIGEN_DIR})", "")
        # Avoid OpenMP_CXX_FLAGS
        replace_in_file(self, "CMakeLists.txt",
                        'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")',
                        'link_libraries(OpenMP::OpenMP_CXX)')
        # Let CudaToolchain handle CUDA architectures
        if Version(self.version) >= "4.6.0":
            replace_in_file(self, "CMakeLists.txt", " CUDA_ARCHITECTURES ", " # CUDA_ARCHITECTURES ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_STATIC_LIB"] = not self.options.shared
        tc.cache_variables["USE_DEBUG"] = self.settings.build_type in ["Debug", "RelWithDebInfo"]
        tc.cache_variables["USE_OPENMP"] = self.options.get_safe("with_openmp", False)
        tc.cache_variables["USE_CUDA"] = self.options.with_cuda
        tc.cache_variables["BUILD_CLI"] = False
        if is_apple_os(self):
            tc.cache_variables["APPLE_OUTPUT_DYLIB"] = True
        tc.variables["_MAJOR_VERSION"] = Version(self.version).major
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=Path(self.source_folder).parent)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LightGBM")
        self.cpp_info.set_property("cmake_target_name", "LightGBM::LightGBM")
        self.cpp_info.libs = ["lib_lightgbm" if is_msvc(self) else "_lightgbm"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi"])
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

