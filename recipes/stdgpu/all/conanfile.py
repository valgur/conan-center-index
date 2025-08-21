import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class StdgpuConan(ConanFile):
    name = "stdgpu"
    description = "Efficient STL-like Data Structures on the GPU"
    license = "Apache-2.0"
    homepage = "https://stotko.github.io/stdgpu/"
    topics = ("cuda", "data-structures", "gpgpu", "gpu", "hip", "openmp", "rocm", "stl", "thrust")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backend": ["cuda", "openmp", "hip"],
        "setup_compiler_flags": [True, False],
        "enable_contract_checks": [None, True, False],
        "use_32_bit_index": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backend": "openmp",
        "setup_compiler_flags": False,
        "enable_contract_checks": None,
        "use_32_bit_index": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    @property
    def _min_cppstd(self):
        if self.version == "1.3.0":
            return 14
        else:
            return 17

    def export_sources(self):
        copy(self, "cmake/*", dst=self.export_sources_folder, src=self.recipe_folder)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.backend != "cuda":
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("thrust/[^1]", transitive_headers=True, transitive_libs=True)
        if self.options.backend == "openmp":
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        elif self.options.backend == "cuda":
            self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if self.options.backend == "cuda":
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        if self.options.backend == "cuda":
            self._utils.validate_cuda_settings(self)
            if Version(self.settings.cuda.version) >= "12.0":
                raise ConanInvalidConfiguration("CUDA 12 and newer are not supported yet.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rm(self, "Findthrust.cmake", "cmake")
        replace_in_file(self, "src/stdgpu/CMakeLists.txt",
                        'install(FILES "${stdgpu_SOURCE_DIR}/cmake/Findthrust.cmake"',
                        'message(TRACE # install(FILES "${stdgpu_SOURCE_DIR}/cmake/Findthrust.cmake"')

    def generate(self):
        tc = CMakeToolchain(self)
        # All the main params from https://github.com/stotko/#integration
        backend = str(self.options.backend).upper()
        tc.cache_variables["STDGPU_BACKEND"] = f"STDGPU_BACKEND_{backend}"
        tc.cache_variables["STDGPU_BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["STDGPU_SETUP_COMPILER_FLAGS"] = self.options.setup_compiler_flags
        tc.cache_variables["STDGPU_TREAT_WARNINGS_AS_ERRORS"] = False
        tc.cache_variables["STDGPU_BUILD_EXAMPLES"] = False
        tc.cache_variables["STDGPU_BUILD_BENCHMARKS"] = False
        tc.cache_variables["STDGPU_BUILD_TESTS"] = False
        if self.options.enable_contract_checks is not None:
            tc.cache_variables["STDGPU_ENABLE_CONTRACT_CHECKS"] = self.options.enable_contract_checks
        tc.cache_variables["STDGPU_USE_32_BIT_INDEX"] = self.options.use_32_bit_index
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("thrust", "cmake_find_mode", "both")
        deps.set_property("thrust", "cmake_file_name", "thrust")
        deps.set_property("thrust", "cmake_target_name", "thrust::thrust")
        deps.generate()

        if self.options.backend == "cuda":
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        if self.options.backend == "cuda":
            replace_in_file(self, os.path.join(self.source_folder, "src/stdgpu/CMakeLists.txt"),
                            "find_package(thrust ",
                            "find_package(CUDAToolkit REQUIRED) #")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = ["stdgpu"]
        thrust_backend = {"cuda": "CUDA", "openmp": "OMP", "hip": "HIP"}[str(self.options.backend)]
        self.cpp_info.defines = [
            f"THRUST_DEVICE_SYSTEM={thrust_backend}",
            f"__THRUST_DEVICE_SYSTEM_NAMESPACE={thrust_backend.lower()}"
        ]
