import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class EigenPyConan(ConanFile):
    name = "eigenpy"
    description = "Efficient bindings between Numpy and Eigen using Boost.Python"
    license = "BSD-2-Clause"
    homepage = "https://github.com/stack-of-tasks/eigenpy"
    topics = ("eigen", "numpy", "python")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "generate_python_stubs": [True, False],
        "with_cholmod": [True, False],
    }
    default_options = {
        "generate_python_stubs": False,
        "with_cholmod": False,
        "boost/*:with_python": True,
        "boost/*:numpy": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("boost/[^1.71.0]", transitive_headers=True, transitive_libs=True)
        self.requires("numpy/[^2.0]", transitive_headers=True)
        if self.options.with_cholmod:
            self.requires("suitesparse-cholmod/[^5.3.0]")

    def validate(self):
        check_min_cppstd(self, 11)
        boost = self.dependencies["boost"].options
        if not boost.with_python or not boost.numpy:
            raise ConanInvalidConfiguration("-o boost/*:with_python=True and -o boost/*:numpy=True is required")

    def build_requirements(self):
        self.tool_requires("jrl-cmakemodules/[*]")
        self.tool_requires("numpy/[^2.0]", visible=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # latest jrl-cmakemodules requires CMake 3.22 or greater
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.10)",
                        "cmake_minimum_required(VERSION 3.22)")
        # get jrl-cmakemodules from Conan
        replace_in_file(self, "CMakeLists.txt", "set(JRL_CMAKE_MODULES ", " # set(JRL_CMAKE_MODULES ")
        # Disable tests
        save(self, "unittest/CMakeLists.txt", "")
        # Fix linking against Boost.Python, since the CMakeDeps output is not translated correctly by the project.
        replace_in_file(self, "CMakeLists.txt",
                        "target_link_boost_python(${PROJECT_NAME} PUBLIC)",
                        "target_link_libraries(${PROJECT_NAME} PUBLIC Boost::python)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["GENERATE_PYTHON_STUBS"] = self.options.generate_python_stubs
        tc.cache_variables["BUILD_WITH_CHOLMOD_SUPPORT"] = self.options.with_cholmod
        tc.cache_variables["BUILD_WITH_ACCELERATE_SUPPORT"] = False  # Requires pre-release Eigen 3.4.90
        tc.cache_variables["SEARCH_FOR_BOOST_PYTHON_ARGS_NAME"] = "python"
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.cache_variables["BUILDING_ROS2_PACKAGE"] = False
        tc.cache_variables["JRL_CMAKE_MODULES"] = self.dependencies.build["jrl-cmakemodules"].cpp_info.builddirs[0].replace("\\", "/")
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("suitesparse-cholmod", "cmake_target_name", "CHOLMOD::CHOLMOD")
        deps.generate()

        if self.options.generate_python_stubs:
            venv = self._utils.PythonVenv(self)
            venv.generate()

    def build(self):
        if self.options.generate_python_stubs:
            self._utils.pip_install(self, ["scipy"])
        cmake = CMake(self)
        cmake.configure()
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

    def _find_installed_site_packages(self):
        return str(next(Path(self.package_folder).rglob("__init__.py")).parent.parent)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "eigenpy")
        self.cpp_info.set_property("cmake_target_name", "eigenpy::eigenpy")
        self.cpp_info.set_property("cmake_config_version_compat", "AnyNewerVersion")
        self.cpp_info.set_property("pkg_config_name", "eigenpy")
        self.cpp_info.libs = ["eigenpy"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        self.cpp_info.requires = ["eigen::eigen", "boost::python", "numpy::numpy"]
        if self.options.with_cholmod:
            self.cpp_info.requires.append("suitesparse-cholmod::suitesparse-cholmod")
        self.runenv_info.prepend_path("PYTHONPATH", self._find_installed_site_packages())
