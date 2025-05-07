import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"

class MicroserviceEssentials(ConanFile):
    name = "microservice-essentials"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/seboste/microservice-essentials"
    license = "MIT"
    description = """microservice-essentials is a portable, independent C++ library that takes care of typical recurring concerns that occur in microservice development."""
    topics = ("microservices", "cloud-native", "request-handling")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tests": [True, False],
        "examples": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tests": False,
        "examples": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        del self.info.options.tests

    def requirements(self):
        if self.options.examples:
            self.requires("cpp-httplib/[^0.14.1]")
            self.requires("nlohmann_json/[^3]")
            self.requires("openssl/[>=3 <4]")
            self.requires("grpc/[^1.50.2]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16.3 <5]")
        if self.options.tests:
            self.test_requires("catch2/[^3.4.0]")
            self.test_requires("nlohmann_json/[^3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["BUILD_TESTING"] = self.options.tests
        tc.variables["BUILD_EXAMPLES"] = self.options.examples
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["microservice-essentials"]
        self.cpp_info.bindirs.extend(["lib"])
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
