import math
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
        self.tool_requires("cmake/[>=3.22 <5]")
        self.tool_requires("numpy/[^2.0]", visible=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["source"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["cmake"], strip_root=True, destination="cmake")
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
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("suitesparse-cholmod", "cmake_target_name", "CHOLMOD::CHOLMOD")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        # The compilation is extremely memory hungry for some reason
        compilation_mem_usage = 4  # GB, approx
        max_jobs = max(math.floor(get_free_memory_gb() / compilation_mem_usage), 1)
        if int(self.conf.get("tools.build:jobs", default=os.cpu_count())) > max_jobs:
            self.output.warning(f"Limiting max jobs to {max_jobs} based on available memory")
            self.conf.define("tools.build:jobs", max_jobs)
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


def get_free_memory_gb():
    try:
        for l in open("/proc/meminfo"):
            if l.startswith("MemAvailable:"):
                return int(l.split()[1]) / 1024**2
    except:
        pass
    try:
        import psutil
        return psutil.virtual_memory().available / 1024**3
    except:
        return 0
