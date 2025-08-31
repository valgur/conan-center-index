import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, check_min_cstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class FbgemmGpuConan(ConanFile):
    name = "fbgemm_gpu"
    description = "FBGEMM_GPU (FBGEMM GPU Kernels Library) is a collection of high-performance PyTorch GPU operator libraries for training and inference."
    license = "BSD-3-Clause"
    homepage = "https://github.com/pytorch/FBGEMM/tree/main/fbgemm_gpu"
    topics = ("matrix", "convolution", "linear-algebra", "machine-learning", "gemm", "gpu")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "variant": ["cuda", "rocm"],
        "target": ["default", "genai", "hstu"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "variant": "cuda",
        "target": "default",
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.variant == "cuda":
            self.options["libtorch"].with_cuda = True
        else:
            del self.settings.cuda
        if self.options.variant == "rocm":
            raise ConanInvalidConfiguration("ROCm variant is not supported yet")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"fbgemm/{self.version}")
        self.requires("libtorch/[^2]")
        self.requires("openmp/system")
        if self.options.variant == "cuda":
            self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
            self._utils.cuda_requires(self, "cusolver", transitive_headers=True, transitive_libs=True)
            self._utils.cuda_requires(self, "nvml-stubs")
            self.requires("nccl/[^2]")
            self.requires("cudnn/[>=8.0 <10]")
            self.requires("cutlass/[*]", transitive_headers=True, transitive_libs=True)
        elif self.options.variant == "rocm":
            # TODO
            self.requires("rocm/[>=5.0]")
            self.requires("hip/[>=5.0]")
            self.requires("rccl/[>=2.0]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25 <5]")
        self.tool_requires("cpython/[^3]")
        if self.options.variant == "cuda":
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, os.path.join(self.source_folder, "third_party"))
        # These are provided externally
        save(self, "fbgemm_gpu/cmake/Asmjit.cmake", "")
        save(self, "fbgemm_gpu/cmake/Fbgemm.cmake", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_fbgemm_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["FBGEMM_LIBRARY_TYPE"] = "shared" if self.options.shared else "static"
        tc.cache_variables["FBGEMM_BUILD_TESTS"] = False
        tc.cache_variables["FBGEMM_BUILD_BENCHMARKS"] = False
        tc.cache_variables["FBGEMM_BUILD_DOCS"] = False
        tc.cache_variables["FBGEMM_BUILD_FBGEMM_GPU"] = True
        tc.cache_variables["FBGEMM_BUILD_TARGET"] = self.options.target
        tc.cache_variables["FBGEMM_BUILD_VARIANT"] = self.options.variant
        tc.cache_variables["PYTHON_EXECUTABLE"] = "python"
        if not self.settings.get_safe("compiler.cstd"):
            tc.variables["CMAKE_C_STANDARD"] = 17
        if is_msvc(self) and self.settings.build_type == "Debug":
            # Avoid "fatal error C1128: number of sections exceeded object file format limit: compile with /bigobj"
            tc.extra_cflags.append("/bigobj")
            tc.extra_cxxflags.append("/bigobj")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.variant == "cuda":
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.extra_cudaflags = ["--extended-lambda"]
            nvcc_tc.generate()

        venv = self._utils.PythonVenv(self)
        venv.generate()

    def build(self):
        self._utils.pip_install(self, ["jinja2"])
        cmake = CMake(self)
        cmake.configure(build_script_folder="fbgemm_gpu")
        self._utils.limit_build_jobs(self, gb_mem_per_job=1.5)
        with self._utils.monitor_memory_usage(self, log_every_n_seconds=10):
            cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "fbgemmLibrary")

        # Core FBGEMM component
        fbgemm = self.cpp_info.components["fbgemm_"]
        fbgemm.set_property("cmake_target_name", "fbgemm")
        fbgemm.libs = ["fbgemm"]
        fbgemm.requires = ["asmjit::asmjit", "cpuinfo::cpuinfo", "openmp::openmp"]
        fbgemm.includedirs.append("include/fbgemm_gpu")
        if not self.options.shared:
            fbgemm.defines = ["FBGEMM_STATIC"]
        if self.options.variant == "cuda":
            fbgemm.defines.append("USE_CUDA")
        elif self.options.variant == "rocm":
            fbgemm.defines.append("USE_ROCM")
        if self.settings.os in ["Linux", "FreeBSD"]:
            fbgemm.system_libs = ["pthread", "dl", "m"]

        def add_component(name, requires=None):
            self.cpp_info.components[name].set_property("cmake_target_name", name)
            self.cpp_info.components[name].libs = [name]
            self.cpp_info.components[name].requires = ["fbgemm_"] + (requires or [])

        add_component("fbgemm_gpu_tbe_utils")
        add_component("fbgemm_gpu_sparse_async_cumsum", ["fbgemm_gpu_tbe_utils"])
        add_component("fbgemm_gpu_tbe_cache", ["asmjit::asmjit"])
        add_component("fbgemm_gpu_tbe_common")
        add_component("fbgemm_gpu_tbe_optimizers")
        add_component("fbgemm_gpu_tbe_inference", ["asmjit::asmjit", "fbgemm_gpu_tbe_cache"])
        add_component("fbgemm_gpu_tbe_training_forward", ["fbgemm_gpu_tbe_common"])
        add_component("fbgemm_gpu_tbe_training_backward", [
            "fbgemm_gpu_tbe_cache", "fbgemm_gpu_tbe_common",
            "fbgemm_gpu_tbe_utils", "fbgemm_gpu_sparse_async_cumsum"
        ])
        add_component("fbgemm_gpu_tbe_training_backward_pt2", [
            "fbgemm_gpu_tbe_cache", "fbgemm_gpu_tbe_common",
            "fbgemm_gpu_tbe_utils", "fbgemm_gpu_sparse_async_cumsum"
        ])
        add_component("fbgemm_gpu_tbe_training_backward_gwd", ["fbgemm_gpu_tbe_training_backward"])
        add_component("fbgemm_gpu_tbe_training_backward_vbe", ["fbgemm_gpu_tbe_training_backward"])
        add_component("fbgemm_gpu_tbe_training_backward_dense", ["fbgemm_gpu_tbe_training_backward"])
        add_component("fbgemm_gpu_tbe_training_backward_split_host", ["fbgemm_gpu_tbe_utils"])
        add_component("fbgemm_gpu_tbe_index_select", ["fbgemm_gpu_sparse_async_cumsum", "fbgemm_gpu_tbe_utils"])
        add_component("fbgemm_gpu_embedding_inplace_ops", [])

        cuda_components = [
            "fbgemm_gpu_tbe_cache",
            "fbgemm_gpu_tbe_inference",
            "fbgemm_gpu_tbe_training_backward",
            "fbgemm_gpu_tbe_training_backward_pt2",
            "fbgemm_gpu_tbe_index_select",
        ]
        if self.options.variant == "cuda":
            for comp in cuda_components:
                self.cpp_info.components[comp].requires.extend([
                    "cudart::cudart_", "nvml-stubs::nvml-stubs", "nccl::nccl", "cudnn::cudnn",
                ])
        elif self.options.variant == "rocm":
            for comp in cuda_components:
                self.cpp_info.components[comp].requires.extend([
                    "rocm::rocm", "hip::hip", "rccl::rccl"
                ])
