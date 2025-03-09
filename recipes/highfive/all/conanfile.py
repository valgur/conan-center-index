from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file, rmdir
import os

required_conan_version = ">=1.54.0"


class HighFiveConan(ConanFile):
    name = "highfive"
    description = "HighFive is a modern header-only C++11 friendly interface for libhdf5."
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/BlueBrain/HighFive"
    topics = ("hdf5", "hdf", "data", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_boost": [True, False],
        "with_eigen": [True, False],
        "with_xtensor": [True, False],
        "with_opencv": [True, False],
        "with_static_hdf5": ["deprecated", True, False],
    }
    default_options = {
        "with_boost": True,
        "with_eigen": True,
        "with_xtensor": True,
        "with_opencv": False,
        "with_static_hdf5": "deprecated",
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("hdf5/1.14.5")
        if self.options.with_boost:
            self.requires("boost/1.86.0")
        if self.options.with_eigen:
            self.requires("eigen/3.4.0")
        if self.options.with_xtensor:
            self.requires("xtensor/0.24.7")
        if self.options.with_opencv:
            self.requires("opencv/4.11.0")

    def package_id(self):
        # INFO: We only set different compiler definitions. The package content is the same.
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.with_static_hdf5 != "deprecated":
            self.output.warning("The option 'with_static_hdf5' is deprecated. Use '-o hdf5/*:shared=True/False' instead.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["USE_BOOST"] = self.options.with_boost
        tc.cache_variables["USE_EIGEN"] = self.options.with_eigen
        tc.cache_variables["USE_XTENSOR"] = self.options.with_xtensor
        tc.cache_variables["USE_OPENCV"] = self.options.with_opencv
        tc.variables["HIGHFIVE_UNIT_TESTS"] = False
        tc.variables["HIGHFIVE_EXAMPLES"] = False
        tc.variables["HIGHFIVE_BUILD_DOCS"] = False
        tc.variables["HIGHFIVE_USE_INSTALL_DEPS"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMake", "HighFiveTargetDeps.cmake"),
            "find_package(Eigen3 NO_MODULE)",
            "find_package(Eigen3 REQUIRED)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMake", "HighFiveTargetDeps.cmake"),
            "EIGEN3_INCLUDE_DIRS",
            "Eigen3_INCLUDE_DIRS",
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "HighFive")
        self.cpp_info.set_property("cmake_target_name", "HighFive")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.requires = ["hdf5::hdf5"]
        if self.options.with_boost:
            self.cpp_info.requires.append("boost::headers")
            self.cpp_info.defines.append("H5_USE_BOOST")
        if self.options.with_eigen:
            self.cpp_info.requires.append("eigen::eigen")
            self.cpp_info.defines.append("H5_USE_EIGEN")
        if self.options.with_xtensor:
            self.cpp_info.requires.append("xtensor::xtensor")
            self.cpp_info.defines.append("H5_USE_XTENSOR")
        if self.options.with_opencv:
            self.cpp_info.requires.append("opencv::opencv")
            self.cpp_info.defines.append("H5_USE_OPENCV")
