import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class XgboostConan(ConanFile):
    name = "xgboost"
    description = ("Scalable, Portable and Distributed Gradient Boosting (GBDT, GBRT or GBM) Library. "
                   "Runs on single machine, Hadoop, Spark, Dask, Flink and DataFlow")
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dmlc/xgboost"
    topics = ("machine-learning", "boosting", "distributed-systems")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "openmp": [True, False],
        "cuda": [True, False],
        "per_thread_default_stream": [True, False],
        "plugin_federated": [True, False],
        "plugin_sycl": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "openmp": True,
        "cuda": False,
        "per_thread_default_stream": True,
        "plugin_federated": False,
        "plugin_sycl": False,
    }
    options_description = {
        "openmp": "Build with OpenMP support",
        # CUDA
        "cuda": "Build with GPU acceleration",
        "per_thread_default_stream": "Build with per-thread default stream (CUDA)",
        # Plugins
        "plugin_federated": "Build with Federated Learning",
        "plugin_sycl": "SYCL plugin (requires Intel icpx compiler)",
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os == "Windows":
            del self.options.plugin_federated
        if self.settings.compiler != "intel-cc":
            del self.options.plugin_sycl

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("plugin_federated"):
            self.requires("grpc/[^1.50.2]")
        if self.options.cuda:
            self.cuda.requires("cudart")
            self.requires("nccl/[^2]")
            self.requires("rmm/[>=24.04.00]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.get_safe("plugin_federated") and not self.options.shared:
            raise ConanInvalidConfiguration("Cannot build static lib with federated learning support")
        if self.options.cuda:
            self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if self.options.get_safe("plugin_federated"):
            self.tool_requires("grpc/<host_version>")
        if self.options.cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["xgboost"], strip_root=True)
        # TODO: unvendor
        get(self, **self.conan_data["sources"][self.version]["dmlc-core"], strip_root=True, destination="dmlc-core")
        get(self, **self.conan_data["sources"][self.version]["gputreeshap"], strip_root=True, destination="gputreeshap")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_OPENMP"] = self.options.openmp
        tc.variables["FORCE_SHARED_CRT"] = not is_msvc_static_runtime(self)
        tc.variables["USE_CUDA"] = self.options.cuda
        tc.variables["USE_NCCL"] = self.options.cuda
        tc.variables["USE_PER_THREAD_DEFAULT_STREAM"] = self.options.per_thread_default_stream
        tc.variables["PLUGIN_RMM"] = self.options.cuda
        tc.variables["PLUGIN_FEDERATED"] = self.options.get_safe("plugin_federated", False)
        tc.variables["PLUGIN_SYCL"] = self.options.get_safe("plugin_sycl", False)
        if self.options.cuda:
            tc.variables["CMAKE_CUDA_RUNTIME_LIBRARY"] = "Shared" if self.dependencies["cudart"].options.shared else "Static"
            tc.variables["NCCL_LIBRARY"] = "nccl::nccl"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("nccl", "cmake_file_name", "Nccl")
        deps.generate()

        if self.options.cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "xgboost")
        self.cpp_info.set_property("cmake_target_name", "xgboost::xgboost")
        self.cpp_info.set_property("pkg_config_name", "xgboost")

        self.cpp_info.libs = ["xgboost"]
        # TODO: unvendor dmlc-core
        self.cpp_info.libs.append("dmlc")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])

        # For the C API
        if stdcpp_library(self):
            self.cpp_info.system_libs.append(stdcpp_library(self))
