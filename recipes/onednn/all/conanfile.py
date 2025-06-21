import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class OneDNNConan(ConanFile):
    name = "onednn"
    description = ("oneAPI Deep Neural Network Library (oneDNN) is an open-source cross-platform "
                   "performance library of basic building blocks for deep learning applications.")
    license = "Apache-2.0"
    homepage = "https://github.com/uxlfoundation/oneDNN"
    topics = ("oneapi", "dnn", "deep-learning", "sycl")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_graph_api": [True, False],
        "workload": ["training", "inference"],
        "cpu_runtime": ["none", "omp", "tbb", "sycl", "threadpool", "seq"],
        "gpu_runtime": ["none", "ocl", "sycl"],
        "gpu_vendor": ["none", "intel", "nvidia", "amd", "generic"],
        "blas_vendor": ["internal", "accelerate", "armpl", "external"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_graph_api": True,
        "workload": "training",
        "cpu_runtime": "omp",
        "gpu_runtime": "none",
        "gpu_vendor": "intel",
        "blas_vendor": "internal",
    }
    options_description = {
        "workload": ("Specifies a set of functionality to be available at build time. "
                     "Designed to decrease the final disk footprint. Valid values:"
                     "- 'training' (the default). Includes all functionality to be enabled."
                     "- 'inference'. Includes only forward propagation kind functionality and their dependencies."),
        "cpu_runtime": ("Specifies the threading runtime for CPU engines. "
                       "Supports OMP (default), TBB or SYCL (SYCL CPU engines)."),
        "gpu_runtime": ("Specifies the threading runtime for GPU engines."
                        "Can be NONE (default; no GPU engines), OCL (OpenCL GPU engines) or SYCL (SYCL GPU engines)."),
        "gpu_vendor": "Specifies target GPU vendor for GPU engines. Can be INTEL (default), NVIDIA or AMD.",
        "blas_vendor": ("BLAS library to use. Options are: "
                        "- 'internal' (default). Use internal BLAS implementation. Recommended in most situations."
                        "- 'accelerate'. Use Apple Accelerate framework on macOS."
                        "- 'armpl'. Use Arm Performance Libraries on Arm platforms."
                        "- 'external'. Use an external BLAS library. This vendor is supported for performance analysis purposes only.")
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.compiler == "intel-cc" and self.settings.compiler.mode in ["icx", "dpcpp"]:
            # Intel compiler users can take advantage of SYCL support
            self.options.cpu_runtime = "sycl"
            self.options.gpu_runtime = "sycl"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.cpu_runtime == "omp":
            self.requires("openmp/system")
        elif self.options.cpu_runtime == "tbb":
            self.requires("onetbb/[>=2021.5 <2023]")
        if self.options.gpu_runtime == "ocl":
            self.requires("opencl-icd-loader/[*]")
            self.requires("opencl-headers/[*]", transitive_headers=True)

        # Unvendored third-party dependencies
        self.requires("level-zero/[^1.17.39]")
        self.requires("spdlog/[^1.11.0]")
        if self.settings.arch in ["x86", "x86_64", "armv8"]:
            self.requires("ittapi/[^3.23.0]")
        if self.settings.arch in ["x86", "x86_64"]:
            self.requires("xbyak/[^7.21]")
        elif self.settings.arch == "armv8":
            self.requires("xbyak_aarch64/[^1.1.2]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.cpu_runtime == "sycl" or self.options.gpu_runtime == "sycl":
            if self.settings.compiler != "intel-cc" or self.settings.compiler.mode not in ["icx", "dpcpp"]:
                raise ConanInvalidConfiguration("SYCL runtime is only supported with Intel icpx or dpcpp compilers.")
            if self.options.cpu_runtime != self.options.gpu_runtime:
                raise ConanInvalidConfiguration("SYCL CPU runtime requires matching SYCL GPU runtime.")
        if self.options.build_graph_api and self.options.gpu_vendor not in ["none", "intel", "nvidia"]:
            raise ConanInvalidConfiguration("enable_graph_api can only be used with gpu_vendor set to 'none', 'intel' or 'nvidia'.")
        if self.options.blas_vendor == "accelerate" and self.settings.os != "Macos":
            raise ConanInvalidConfiguration("blas_vendor=accelerate is only supported on macOS.")
        if self.options.blas_vendor == "armpl":
            raise ConanInvalidConfiguration("blas_vendor=armpl is not yet supported.")
        if self.options.blas_vendor == "external":
            raise ConanInvalidConfiguration("blas_vendor=external is not yet supported.")

    def source(self):
        info = self.conan_data["sources"][self.version]
        get(self, **info["onednn"], strip_root=True)
        apply_conandata_patches(self)
        rmdir(self, "third_party/ittnotify")
        rmdir(self, "third_party/level_zero")
        rmdir(self, "third_party/spdlog")
        rmdir(self, "third_party/xbyak")
        rmdir(self, "third_party/xbyak_aarch64")
        # Replace two vendored headers with the latest versions from intel/compute-runtime
        download(self, **info["ze_intel_gpu.h"], filename="third_party/level_zero/ze_intel_gpu.h")
        download(self, **info["ze_stypes.h"], filename="third_party/level_zero/ze_stypes.h")

    def generate(self):
        # https://github.com/uxlfoundation/oneDNN/blob/v3.8.1/cmake/options.cmake
        tc = CMakeToolchain(self)
        tc.cache_variables["DNNL_LIBRARY_TYPE"] = "SHARED" if self.options.shared else "STATIC"
        tc.cache_variables["DNNL_BUILD_DOC"] = False
        tc.cache_variables["DNNL_BUILD_EXAMPLES"] = False
        tc.cache_variables["DNNL_BUILD_TESTS"] = False
        tc.cache_variables["ONEDNN_BUILD_GRAPH"] = self.options.build_graph_api
        tc.cache_variables["DNNL_ENABLE_WORKLOAD"] = self.options.workload.value.upper()
        tc.cache_variables["DNNL_CPU_RUNTIME"] = self.options.cpu_runtime.value.upper()
        tc.cache_variables["DNNL_GPU_RUNTIME"] = self.options.gpu_runtime.value.upper()
        tc.cache_variables["DNNL_GPU_VENDOR"] = self.options.gpu_vendor.value.upper()
        tc.cache_variables["DNNL_BLAS_VENDOR"] = {"internal": "NONE", "accelerate": "ACCELERATE", "external": "ANY"}[self.options.blas_vendor.value]
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "THIRD-PARTY-PROGRAMS", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "dnnl")
        self.cpp_info.set_property("cmake_target_name", "DNNL::dnnl")
        self.cpp_info.libs = ["dnnl"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread", "dl"]

        # For the dnnl C API
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.system_libs.append(stdcpp_library(self))

        if self.options.cpu_runtime == "sycl" or self.options.gpu_runtime == "sycl":
            self.cpp_info.cxxflags.append("-fsycl")
            if self.options.gpu_vendor == "nvidia":
                # TODO: use dedicated CUDA packages
                if not self.options.shared:
                    self.cpp_info.system_libs.extend(["cublas", "cublasLt", "cudnn"])

        if self.options.blas_vendor == "accelerate":
            self.cpp_info.frameworks = ["Accelerate"]
