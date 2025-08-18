import os

from conan import ConanFile
from conan.tools.build import stdcpp_library, check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class FaissRecipe(ConanFile):
    name = "faiss"
    description = "Faiss - a library for efficient similarity search and clustering of dense vectors"
    license = "MIT"
    homepage = "https://github.com/facebookresearch/faiss"
    topics = ("approximate-nearest-neighbor", "similarity-search", "clustering", "gpu")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "opt_level": ["generic", "avx2", "avx512", "avx512_spr", "sve"],
        "c_api": [True, False],
        "lto": [True, False],
        "with_cuda": [True, False],
        "with_mkl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "opt_level": "avx2",
        "c_api": False,
        "lto": False,
        "with_cuda": False,
        "with_mkl": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch != "x86_64":
            del self.options.opt_level

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["openblas"].use_openmp = True
        self.options["openblas"].use_thread = False
        self.options["openblas"].use_locking = False
        self.options["openblas"].num_threads = 512
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # #include <omp.h> and #pragma omp is used in multiple public headers
        self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_mkl:
            self.requires("onemkl/[*]")
        else:
            self.requires("openblas/[>=0.3.28 <1]")
        if self.options.with_cuda:
            self._utils.cuda_requires(self, "cudart")
            self._utils.cuda_requires(self, "cublas")
            self._utils.cuda_requires(self, "curand")
            self.requires(f"cuda-profiler-api/[~{self.settings.cuda.version}]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.with_cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <5]")
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],  strip_root=True)
        replace_in_file(self, "faiss/CMakeLists.txt", "POSITION_INDEPENDENT_CODE ON", "")
        # Fix a missing cuRAND dependency: faiss/gpu/impl/IcmEncoder.cu uses curand_kernel.h
        replace_in_file(self, "faiss/gpu/CMakeLists.txt",
                        "set(CUDA_LIBS CUDA::cudart CUDA::cublas)",
                        "find_package(cuda-profiler-api REQUIRED)\n"
                        "set(CUDA_LIBS CUDA::cudart CUDA::cublas CUDA::curand cuda-profiler-api::cuda-profiler-api)")
        # Use the more precise MKL::MKL target instead of everything packaged by the onemkl recipe
        replace_in_file(self, "faiss/CMakeLists.txt", "${MKL_LIBRARIES}", "MKL::MKL")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FAISS_OPT_LEVEL"] = self.options.get_safe("opt_level", "generic")
        tc.cache_variables["FAISS_c_api"] = self.options.c_api
        tc.cache_variables["FAISS_ENABLE_GPU"] = self.options.with_cuda
        tc.cache_variables["FAISS_ENABLE_CUVS"] = False  # TODO: rapidsai/cuvs
        tc.cache_variables["FAISS_ENABLE_MKL"] = self.options.with_mkl
        tc.cache_variables["FAISS_ENABLE_PYTHON"] = False
        tc.cache_variables["FAISS_ENABLE_EXTRAS"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["FAISS_USE_LTO"] = self.options.lto
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    @property
    def _enabled_opt_levels(self):
        levels = ["generic", "avx2", "avx512", "avx512_spr", "sve"]
        return levels[:levels.index(self.options.get_safe("opt_level", "generic")) + 1]

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "faiss")

        for level in self._enabled_opt_levels:
            lib = "faiss" if level == "generic" else f"faiss_{level}"
            component = self.cpp_info.components["faiss_" if level != "generic" else lib]
            component.set_property("cmake_target_name", lib)
            component.libs = [lib]
            component.requires = ["openmp::openmp"]
            if self.options.with_mkl:
                component.requires.append("onemkl::mkl")
            else:
                component.requires.append("openblas::openblas")
            if self.options.with_cuda:
                component.requires.extend([
                    "cudart::cudart_",
                    "cublas::cublas_",
                    "curand::curand",
                    "cuda-profiler-api::cuda-profiler-api",
                ])
            if self.settings.os in ["Linux", "FreeBSD"]:
                component.system_libs.append("m")
            if self.options.c_api:
                lib_c = "faiss_c" if level == "generic" else f"faiss_c_{level}"
                component_c = self.cpp_info.components[lib_c]
                component_c.set_property("cmake_target_name", lib_c)
                component_c.libs = [lib_c]
                component_c.requires = ["faiss_" if level != "generic" else lib]
                if not self.options.shared and stdcpp_library(self):
                    component_c.system_libs.append(stdcpp_library(self))

    def compatibility(self):
        return [{"options": [("opt_level", level)]} for level in self._enabled_opt_levels]
