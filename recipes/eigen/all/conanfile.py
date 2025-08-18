import os

from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class EigenConan(ConanFile):
    name = "eigen"
    description = ("Eigen is a C++ template library for linear algebra: matrices, vectors,"
                   " numerical solvers, and related algorithms.")
    license = "MPL-2.0 AND BSD-3-Clause AND LGPL-2.1-or-later"
    topics = ("algebra", "linear-algebra", "matrix", "vector", "numerical", "header-only")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://eigen.tuxfamily.org"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "MPL2_only": [True, False],
        # TODO: add use_blas, use_lapack for Eigen 3.3+: https://eigen.tuxfamily.org/dox-devel/TopicUsingBlasLapack.html
    }
    default_options = {
        # No longer applicable in Eigen 4.x.
        # As of Eigen 3.4.0, only the following are LGPL:
        #   Eigen/src/SparseCholesky/SimplicialCholesky.h
        #   Eigen/src/OrderingMethods/Amd.h
        #   unsupported/Eigen/src/IterativeSolvers/*
        "MPL2_only": False,
    }

    @property
    def _is_v4(self):
        return Version(self.version).major >= 4

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self._is_v4:
            del self.options.MPL2_only

    def configure(self):
        if not self._is_v4:
            # Based on https://salsa.debian.org/science-team/eigen3/-/blob/debian/3.4.0-5/debian/copyright
            if self.options.MPL2_only:
                self.license = "MPL-2.0 AND BSD-3-Clause"
            else:
                self.license = "MPL-2.0 AND BSD-3-Clause AND LGPL-2.1-or-later"
        else:
            self.license = "MPL-2.0 AND BSD-3-Clause AND Minpack AND Apache-2.0"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        if not self._is_v4:
            self.output.info("Patching DisableStupidWarnings.h to the latest version to avoid warnings from newer compiler versions")
            path = "Eigen/src/Core/util/DisableStupidWarnings.h"
            assert os.path.isfile(path)
            download(self, **self.conan_data["disable_stupid_warnings_h"], filename=path)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["EIGEN_BUILD_BLAS"] = False
        tc.cache_variables["EIGEN_BUILD_LAPACK"] = False
        tc.cache_variables["BUILD_TESTING"] = not self.conf.get("tools.build:skip_test", default=True, check_type=bool)
        tc.cache_variables["EIGEN_TEST_NOQT"] = True
        tc.cache_variables["EIGEN_BUILD_DOC"] = False
        tc.cache_variables["EIGEN_BUILD_DEMOS"] = False
        tc.cache_variables["EIGEN_BUILD_PKGCONFIG"] = False
        tc.cache_variables["EIGEN_BUILD_CMAKE_PACKAGE"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Eigen3")
        self.cpp_info.set_property("cmake_target_name", "Eigen3::Eigen")
        self.cpp_info.set_property("pkg_config_name", "eigen3")
        self.cpp_info.includedirs = ["include/eigen3"]
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if self.options.get_safe("MPL2_only"):
            self.cpp_info.defines = ["EIGEN_MPL2_ONLY"]
