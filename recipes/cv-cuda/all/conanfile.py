import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CvCudaConan(ConanFile):
    name = "cv-cuda"
    description = "CV-CUDA is an open-source, GPU-accelerated library for cloud-scale image processing and computer vision."
    license = "Apache-2.0"
    homepage = "https://github.com/CVCUDA/CV-CUDA"
    topics = ("machine-learning", "computer-vision", "gpu", "cuda", "image-processing", "nvidia", "bytedance")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cublas")
        self.cuda.requires("cusolver")
        # cuRAND headers are only used to define curandState*
        self.cuda.requires("curand", libs=False)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("CV-CUDA is only supported on Linux")
        check_min_cppstd(self, 17)
        self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20.1]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "3rdparty")
        save(self, "3rdparty/CMakeLists.txt", "")
        # Add a missing curand dep
        replace_in_file(self, "src/cvcuda/priv/CMakeLists.txt", "CUDA::cudart_static", "CUDA::cudart_static CUDA::curand_static")
        replace_in_file(self, "src/cvcuda/priv/legacy/CMakeLists.txt", "CUDA::cudart_static", "CUDA::cudart_static CUDA::curand_static")
        # Don't add a triplet subdir to lib/
        replace_in_file(self, "cmake/ConfigBuildTree.cmake", "set(CMAKE_INSTALL_LIBDIR", "# set(CMAKE_INSTALL_LIBDIR")
        replace_in_file(self, "cmake/ConfigBuildTree.cmake", "set(CMAKE_INSTALL_RPATH", "# set(CMAKE_INSTALL_RPATH")
        replace_in_file(self, "src/nvcv/cmake/ConfigBuildTree.cmake", "set(CMAKE_INSTALL_LIBDIR", "# set(CMAKE_INSTALL_LIBDIR")
        replace_in_file(self, "src/nvcv/cmake/ConfigBuildTree.cmake", "set(CMAKE_INSTALL_RPATH", "# set(CMAKE_INSTALL_RPATH")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CCACHE_EXEC"] = False
        tc.cache_variables["USE_CMAKE_CUDA_ARCHITECTURES"] = True
        tc.cache_variables["ENABLE_COMPAT_OLD_GLIBC"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "doc"))

    def package_info(self):
        # nvcv_types-config.cmake is also installed by the project
        self.cpp_info.set_property("cmake_file_name", "cvcuda")

        self.cpp_info.components["cvcuda"].set_property("cmake_target_name", "cvcuda")
        self.cpp_info.components["cvcuda"].libs = ["cvcuda"]
        self.cpp_info.components["cvcuda"].requires = [
            "nvcv_types",
            "cudart::cudart_",
            "cublas::cublas_",
            "cusolver::cusolver_",
            "curand::curand",
        ]

        self.cpp_info.components["nvcv_types"].set_property("cmake_target_name", "nvcv_types")
        self.cpp_info.components["nvcv_types"].libs = ["nvcv_types"]
        self.cpp_info.components["nvcv_types"].requires = ["cudart::cudart_"]

        if not self.options.shared:
            if self.settings.os == "Linux":
                self.cpp_info.components["cvcuda"].system_libs = ["m", "pthread", "dl", "rt"]
                self.cpp_info.components["nvcv_types"].system_libs = ["m", "dl"]
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.components["cvcuda"].system_libs.append(libcxx)
                self.cpp_info.components["nvcv_types"].system_libs.append(libcxx)
