import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain, CMakeDeps
from conan.tools.files import get, rmdir


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

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.81.0")
        self.requires("span-lite/0.10.3")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        # CMake >= 3.18 is required
        # https://github.com/cmannett85/arg_router/blob/449567723d6c0e9db0a4c89277066c9a53b299fa/CMakeLists.txt#L5
        self.tool_requires("cmake/3.25.3")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["INSTALLATION_ONLY"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        # Folders not used for header-only
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
