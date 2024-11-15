import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.53.0"


class AwsCCompression(ConanFile):
    name = "aws-c-compression"
    description = "C99 implementation of huffman encoding/decoding"
    topics = ("aws", "amazon", "cloud", "compression", "huffman", )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/awslabs/aws-c-compression"
    license = "Apache-2.0"
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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.version == "0.2.18":
            self.requires("aws-c-common/0.9.15", transitive_headers=True, transitive_libs=True)
        if self.version == "0.2.14":
            self.requires("aws-c-common/0.6.11", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "aws-c-compression"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "aws-c-compression")
        self.cpp_info.set_property("cmake_target_name", "AWS::aws-c-compression")
        self.cpp_info.libs = ["aws-c-compression"]
        if self.options.shared:
            self.cpp_info.defines.append("AWS_COMPRESSION_USE_IMPORT_EXPORT")
