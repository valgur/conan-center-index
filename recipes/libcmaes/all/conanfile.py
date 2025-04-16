import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.cmake.cmakedeps.cmakedeps import CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibcmaesConan(ConanFile):
    name = "libcmaes"
    description = (
        "libcmaes is a multithreaded C++11 library for high performance blackbox stochastic optimization"
        " using the CMA-ES algorithm for Covariance Matrix Adaptation Evolution Strategy"
    )
    license = "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CMA-ES/libcmaes"
    topics = ("optimization", "minimization")

    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "surrog": [True, False],
        "with_glog": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "surrog": True,
        "with_glog": False,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_glog:
            self.requires("glog/[>=0.6.0 <1]", transitive_headers=True, transitive_libs=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LIBCMAES_BUILD_EXAMPLES"] = False
        tc.cache_variables["LIBCMAES_BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["LIBCMAES_USE_OPENMP"] = self.options.with_openmp
        tc.cache_variables["LIBCMAES_ENABLE_SURROG"] = self.options.surrog
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libcmaes")
        self.cpp_info.set_property("cmake_target_name", "libcmaes::cmaes")
        self.cpp_info.set_property("pkg_config_name", "libcmaes")
        self.cpp_info.libs = ["cmaes"]

        if self.options.with_glog:
            self.cpp_info.defines.append("HAVE_GLOG")
