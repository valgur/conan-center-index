import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class NvBenchConan(ConanFile):
    name = "nvbench"
    description = "NVBench: CUDA Kernel Benchmarking Library"
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/nvbench"
    topics = ("cuda", "benchmarking", "nvidia")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cupti/*:shared": True,
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
        self.cuda.requires("nvml-stubs", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cupti", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/[*]")
        self.requires("nlohmann_json/[^3]")

    def validate(self):
        check_min_cppstd(self, 17)
        self.cuda.validate_settings()
        if not self.dependencies["cupti"].options.shared:
            raise ConanInvalidConfiguration("nvbench requires cupti to be built as a shared library")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        # Fix linking against CUPTI
        replace_in_file(self, "cmake/NVBenchCUPTI.cmake", "nvbench_add_cupti_dep(", "# nvbench_add_cupti_dep")
        replace_in_file(self, "cmake/NVBenchCUPTI.cmake", "target_include_directories(nvbench::cupti", "message(TRACE ")
        # nlohmann_json
        replace_in_file(self, "cmake/NVBenchDependencies.cmake",
                        "add_library(nvbench_json",
                        "find_package(nlohmann_json REQUIRED)\n"
                        "add_library(nvbench_json")
        # Fix missing libcxx linking
        replace_in_file(self, "exec/CMakeLists.txt",
                        "set_target_properties(nvbench.ctl PROPERTIES",
                        'set_target_properties(nvbench.ctl PROPERTIES LINKER_LANGUAGE CXX')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("cupti::nvperf_target", "cmake_target_name", "nvbench::nvperf_target")
        deps.set_property("cupti::nvperf_host", "cmake_target_name", "nvbench::nvperf_host")
        deps.set_property("cupti::cupti_", "cmake_target_name", "nvbench::cupti")
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.generate()

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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # Move .o files
        for obj_file in Path(self.package_folder, "lib").rglob("*.o"):
            obj_file.rename(Path(self.package_folder, "lib", obj_file.name))
        rmdir(self, next(Path(self.package_folder, "lib").glob("objects-*")))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvbench")

        self.cpp_info.components["nvbench_"].set_property("cmake_target_name", "nvbench::nvbench")
        self.cpp_info.components["nvbench_"].libs = ["nvbench"]
        self.cpp_info.components["nvbench_"].requires = [
            "cudart::cudart_",
            "nvml-stubs::nvml-stubs",
            "cupti::cupti_",
            "fmt::fmt",
            "nlohmann_json::nlohmann_json"
        ]

        self.cpp_info.components["main"].set_property("cmake_target_name", "nvbench::main")
        self.cpp_info.components["main"].objects = ["lib/main.cu.o"]
        self.cpp_info.components["main"].requires = ["nvbench_"]
        self.cpp_info.components["main"].defines.append("FMT_USE_BITINT=0")
        if not self.settings.compiler == "msvc":
            self.cpp_info.components["main"].cxxflags = [
                "-Wall",
                "-Wcast-qual",
                "-Wconversion",
                "-Wextra",
                "-Wno-gnu-line-marker",
                "-Woverloaded-virtual",
                "-Wpointer-arith",
                "-Wunused-parameter",
                "-Wvla",
                "-Wno-deprecated-gpu-targets",
                # "-Werror",
            ]
            # The following CUDA flags are also set:
            # -Wno-deprecated-gpu-targets
            # -Xcompiler=-Wall
            # -Xcompiler=-Wcast-qual
            # -Xcompiler=-Wconversion
            # -Xcompiler=-Werror
            # -Xcompiler=-Wextra
            # -Xcompiler=-Wno-gnu-line-marker
            # -Xcompiler=-Woverloaded-virtual
            # -Xcompiler=-Wpointer-arith
            # -Xcompiler=-Wunused-parameter
            # -Xcompiler=-Wvla
            # -Xcudafe=--display_error_number
            # -Xcudafe=--promote_warnings
