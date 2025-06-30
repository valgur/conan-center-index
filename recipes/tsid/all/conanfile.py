import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class TsidConan(ConanFile):
    name = "tsid"
    description = ("TSID is a C++ library for optimization-based inverse-dynamics control "
                   "based on the rigid multi-body dynamics library Pinocchio.")
    license = "BSD-2-Clause"
    homepage = "https://github.com/stack-of-tasks/tsid"
    topics = ("robotics", "control", "inverse-dynamics", "optimization", "pinocchio")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "python_bindings": [True, False],
        "with_osqp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "python_bindings": False,
        "with_osqp": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.python_bindings:
            self.options["pinocchio"].python_bindings = True
            self.options["boost"].with_python = True
            self.options["boost"].numpy = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("pinocchio/[^3.7.0]", transitive_headers=True, transitive_libs=True)
        self.requires("eiquadprog/[^1.2.9]", transitive_headers=True)
        if self.options.with_osqp:
            self.requires("osqp-eigen/[>=0.10 <1]", transitive_headers=True, transitive_libs=True)
        # TODO: proxqp support
        # TODO: qpmad support
        if self.options.python_bindings:
            # eigenpy adds cpython and numpy deps transitively
            self.requires("eigenpy/[^3.11.0]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("jrl-cmakemodules/[*]")
        if self.options.python_bindings:
            self.tool_requires("eigenpy/[^3.11.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # latest jrl-cmakemodules requires CMake 3.22 or greater
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.10)",
                        "cmake_minimum_required(VERSION 3.22)")
        # get jrl-cmakemodules from Conan
        replace_in_file(self, "CMakeLists.txt", "set(JRL_CMAKE_MODULES ", " # set(JRL_CMAKE_MODULES ")
        # Add missing findpython() call to set PYTHON_EXT_SUFFIX var
        bindings_cmake = Path("bindings/python/CMakeLists.txt")
        bindings_cmake.write_text("include(${JRL_CMAKE_MODULES}/python.cmake)\nfindpython()\n" + bindings_cmake.read_text())

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_PYTHON_INTERFACE"] = self.options.python_bindings
        tc.cache_variables["BUILD_WITH_OSQP"] = self.options.with_osqp
        tc.cache_variables["JRL_CMAKE_MODULES"] = self.dependencies.build["jrl-cmakemodules"].cpp_info.builddirs[0].replace("\\", "/")
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_qpmad"] = True
        tc.cache_variables["BUILDING_ROS2_PACKAGE"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_BENCHMARK"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="tsid")
        # Compilation with EigenPy has a very high memory footprint, so limit the max number of jobs
        if self.options.python_bindings:
            self._utils.limit_build_jobs(self, gb_mem_per_job=4)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tsid")
        self.cpp_info.set_property("cmake_target_name", "tsid::tsid")
        self.cpp_info.set_property("pkg_config_name", "tsid")
        self.cpp_info.libs = ["tsid"]
        if self.options.with_osqp:
            self.cpp_info.defines.append("TSID_WITH_OSQP")
        if self.options.get_safe("with_proxqp"):
            self.cpp_info.defines.append("TSID_WITH_PROXSUITE")
        if self.options.get_safe("with_qpmad"):
            self.cpp_info.defines.append("TSID_WITH_QPMAD")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
