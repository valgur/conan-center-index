import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.0"

class CmaesConan(ConanFile):
    name = "cmaes"
    description = (
        "A multithreaded C++11 library for high performance blackbox stochastic optimization "
        "using the CMA-ES algorithm for Covariance Matrix Adaptation Evolution Strategy"
    )
    license = "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CMA-ES/libcmaes"
    topics = ("cmaes", "minimization")
    package_type = "library"

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "openmp": True,
    }

    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def validate_build(self):
        if self.settings.compiler == "msvc":
            raise ConanInvalidConfiguration("cmaes does not support MSVC")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required (VERSION 3.1)",
                        "cmake_minimum_required (VERSION 3.5)")

    def requirements(self):
        # Transitive header: https://github.com/CMA-ES/libcmaes/blob/v0.10/include/libcmaes/eigenmvn.h#L36
        self.requires("eigen/3.4.0", transitive_headers=True)
        if self.options.openmp:
            # pragma omp is used in genopheno.h public header
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LIBCMAES_BUILD_EXAMPLES"] = False
        tc.cache_variables["LIBCMAES_BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["LIBCMAES_USE_OPENMP"] = self.options.openmp
        tc.cache_variables["LIBCMAES_BUILD_PYTHON"] = False
        tc.cache_variables["LIBCMAES_BUILD_TESTS"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libcmaes")
        self.cpp_info.set_property("cmake_target_name", "libcmaes::cmaes")
        self.cpp_info.set_property("pkg_config_name", "libcmaes")
        self.cpp_info.libs = ["cmaes"]
