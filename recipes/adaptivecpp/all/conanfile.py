import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class AdaptiveCppConan(ConanFile):
    name = "adaptivecpp"
    description = ("Compiler for multiple programming models (SYCL, C++ standard parallelism, HIP/CUDA) for CPUs and GPUs from all vendors: "
                   "The independent, community-driven compiler for C++-based heterogeneous programming models. "
                   "Lets applications adapt themselves to all the hardware in the system - even at runtime!")
    license = "BSD-2-Clause"
    homepage = "https://github.com/AdaptiveCpp/AdaptiveCpp"
    topics = ("compiler", "parallelism", "gpgpu", "sycl", "hip", "cuda", "hipsycl")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "cuda": [True, False],
        "rocm": [True, False],
        "opencl": [True, False],
        "cmake_name": ["AdaptiveCpp", "hipSYCL", "OpenSYCL"],
    }
    default_options = {
        "cuda": False,
        "rocm": False,
        "opencl": False,
        "cmake_name": "AdaptiveCpp",
        "boost/*:with_fiber": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if not self.options.cuda:
            del self.settings.cuda

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71]", transitive_headers=True, transitive_libs=True)
        self.requires("llvm-core/[>=19]", transitive_headers=True, transitive_libs=True)
        self.requires("clang/[>=19]", transitive_headers=True, libs=False)
        self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        self.requires("libnuma/[^2.0.14]")
        if self.options.cuda:
            self._utils.cuda_requires(self, "cudart")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("The recipe currently only supports Linux.")
        if self.options.cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        self.tool_requires("clang/<host_version>")

    def validate_build(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["WITH_CUDA_BACKEND"] = self.options.cuda
        tc.cache_variables["WITH_ROCM_BACKEND"] = self.options.rocm
        tc.cache_variables["WITH_OPENCL_BACKEND"] = self.options.opencl
        tc.cache_variables["ACPP_EXPERIMENTAL_LLVM"] = True
        tc.cache_variables["LLVM_LIBRARY"] = "LLVM"
        tc.generate()

        deps = CMakeDeps(self)
        if not self.dependencies["llvm-core"].options.monolithic:
            deps.set_property("llvm-core", "cmake_target_aliases", ["LLVM"])
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        for cmake_name in ["AdaptiveCpp", "hipSYCL", "OpenSYCL"]:
            cmake_dir = os.path.join(self.package_folder, "lib", "cmake", cmake_name)
            name_lower = cmake_name.lower()
            rm(self, "*-config-version.cmake", cmake_dir)
            rm(self, "*-targets*.cmake", cmake_dir)
            rename(self, os.path.join(cmake_dir, f"{name_lower}-config.cmake"), os.path.join(cmake_dir, f"{name_lower}-vars.cmake"))
            replace_in_file(self, os.path.join(cmake_dir, f"{name_lower}-vars.cmake"), "include(", "# include(")
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        cmake_name = self.options.cmake_name.value
        self.cpp_info.set_property("cmake_file_name", cmake_name)

        self.cpp_info.components["acpp-common"].set_property("cmake_target_name", f"{cmake_name}::acpp-common")
        self.cpp_info.components["acpp-common"].libs = ["acpp-common"]
        self.cpp_info.components["acpp-common"].includedirs.append("include/AdaptiveCpp")
        self.cpp_info.components["acpp-common"].builddirs = [f"lib/cmake/{cmake_name}"]
        self.cpp_info.set_property("cmake_build_modules", [f"lib/cmake/{cmake_name}/{cmake_name.lower()}-vars.cmake"])

        self.cpp_info.components["acpp-rt"].set_property("cmake_target_name", f"{cmake_name}::acpp-rt")
        self.cpp_info.components["acpp-rt"].libs = ["acpp-rt"]
        self.cpp_info.components["acpp-rt"].requires = ["acpp-common"]

        self.cpp_info.components["_runtime_deps"].requires = [
            "boost::fiber",
            "llvm-core::llvm-core",
            "clang::clang",
            "openmp::openmp",
            "libnuma::libnuma",
        ]
        if self.options.cuda:
            self.cpp_info.components["_runtime_deps"].requires.append("cudart::cudart_")
