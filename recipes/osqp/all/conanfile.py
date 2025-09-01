import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class OsqpConan(ConanFile):
    name = "osqp"
    package_type = "library"
    description = "The OSQP (Operator Splitting Quadratic Program) solver is a numerical optimization package."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://osqp.org/"
    topics = ("machine-learning", "control", "optimization", "svm", "solver", "lasso", "portfolio-optimization",
              "numerical-optimization", "quadratic-programming", "convex-optimization", "model-predictive-control")
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backend": ["builtin", "cuda", "mkl"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backend": "builtin",
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.backend != "cuda":
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.backend == "cuda":
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")
            self.cuda.requires("cusparse")
        elif self.options.backend == "mkl":
            self.requires("onemkl/[*]")

    def validate(self):
        if Version(self.version) < "1.0" and self.options.backend != "builtin":
            raise ConanInvalidConfiguration("Alternative backends are only supported in osqp >= 1.0.0")
        if self.options.backend == "cuda":
            self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if self.options.backend == "cuda":
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])
        # CMake v4 support
        if Version(self.version) < "1.0.0":
            for cmakelists in ["CMakeLists.txt", "lin_sys/direct/qdldl/qdldl_sources/CMakeLists.txt"]:
                replace_in_file(self, cmakelists,
                                "cmake_minimum_required (VERSION 3.2)",
                                "cmake_minimum_required (VERSION 3.5)")
        # Don't set CUDA architectures
        if Version(self.version) >= "1.0.0":
            replace_in_file(self, "CMakeLists.txt",
                            "set(CMAKE_CUDA_ARCHITECTURES ",
                            "# set(CMAKE_CUDA_ARCHITECTURES ")
        if Version(self.version) >= "1.0.0":
            replace_in_file(self, "algebra/mkl/CMakeLists.txt", "$<TARGET_PROPERTY:MKL::MKL", ") #")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OSQP_ALGEBRA_BACKEND"] = self.options.backend
        tc.variables["UNITTESTS"] = not self.conf.get("tools.build:skip_test", default=True, check_type=bool)
        tc.variables["PRINTING"] = True
        tc.variables["PROFILING"] = True
        tc.variables["CTRLC"] = True
        tc.variables["DFLOAT"] = False
        tc.variables["DLONG"] = True
        tc.variables["COVERAGE"] = False
        tc.variables["ENABLE_MKL_PARDISO"] = True
        tc.variables["OSQP_BUILD_DEMO_EXE"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.backend == "cuda":
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        if self.settings.os == "Windows":
            if self.options.shared:
                rm(self, "qdldl.dll", os.path.join(self.package_folder, "bin"))
            else:
                rmdir(self, os.path.join(self.package_folder, "bin"))
        else:
            if self.options.shared:
                rm(self, "*.a", os.path.join(self.package_folder, "lib"))
            else:
                rm(self, "*.so", os.path.join(self.package_folder, "lib"))
                rm(self, "*.dylib", os.path.join(self.package_folder, "lib"))

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "include", "qdldl"))
        rm(self, "*qdldl.*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "osqp")
        self.cpp_info.set_property("cmake_target_name", "osqp::osqp")
        self.cpp_info.libs = ["osqpstatic" if Version(self.version) >= "1.0" and not self.options.shared else "osqp"]
        self.cpp_info.includedirs.append("include/osqp")
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
