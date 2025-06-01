import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class ArgRouterRecipe(ConanFile):
    name = "arg_router"
    license = "BSL-1.0"
    homepage = "https://github.com/cmannett85/arg_router"
    url = "https://github.com/conan-io/conan-center-index"
    description = "C++ command line argument parsing and routing."
    topics = ("cpp", "command-line", "argument-parser", "header-only")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "header-library"
    no_copy_source = True

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.74.0]", libs=False)
        self.requires("span-lite/[>=0.10.3 <1]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25.3 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["INSTALLATION_ONLY"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "arg_router")
        self.cpp_info.set_property("cmake_target_name", "arg_router::arg_router")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
