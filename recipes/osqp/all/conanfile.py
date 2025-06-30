import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
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
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])
        # CMake v4 support
        if Version(self.version) < "1.0.0":
            for cmakelists in ["CMakeLists.txt", "lin_sys/direct/qdldl/qdldl_sources/CMakeLists.txt"]:
                replace_in_file(self, cmakelists,
                                "cmake_minimum_required (VERSION 3.2)",
                                "cmake_minimum_required (VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["UNITTESTS"] = not self.conf.get("tools.build:skip_test", default=True, check_type=bool)
        tc.variables["PRINTING"] = True
        tc.variables["PROFILING"] = True
        tc.variables["CTRLC"] = True
        tc.variables["DFLOAT"] = False
        tc.variables["DLONG"] = True
        tc.variables["COVERAGE"] = False
        tc.variables["ENABLE_MKL_PARDISO"] = True
        tc.generate()

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
        self.cpp_info.libs = ["osqp"]
        self.cpp_info.includedirs.append("include/osqp")
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
