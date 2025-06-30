import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class OSQPEigenConan(ConanFile):
    name = "osqp-eigen"
    description = "short description"
    license = "BSD-3-Clause"
    homepage = "https://github.com/robotology/osqp-eigen"
    topics = ("optimization", "quadratic-programming", "convex-optimization", "qp", "osqp")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("osqp/[>=0.6 <2]", transitive_headers=True, transitive_libs=True)
        self.requires("eigen/3.4.0", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _osqp_is_v1(self):
        return self.dependencies["osqp"].ref.version >= "1.0"

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["OSQP_IS_V1"] = self._osqp_is_v1
        tc.cache_variables["OSQP_IS_V1_FINAL"] = self._osqp_is_v1
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OsqpEigen")
        self.cpp_info.set_property("cmake_target_name", "OsqpEigen::OsqpEigen")
        suffix = "d" if self.settings.compiler == "msvc" and self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = ["OsqpEigen" + suffix]
        if self._osqp_is_v1:
            self.cpp_info.defines = ["OSQP_EIGEN_OSQP_IS_V1", "OSQP_EIGEN_OSQP_IS_V1_FINAL"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
