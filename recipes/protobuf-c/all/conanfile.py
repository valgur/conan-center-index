import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ProtobufCConan(ConanFile):
    name = "protobuf-c"
    description = "Protocol Buffers implementation in C"
    license = "LicenseRef-LICENSE"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/protobuf-c/protobuf-c"
    topics = ("protocol-buffers", "protocol-compiler", "serialization", "protocol-compiler")
    # package_type = "library"
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "with_proto3": [True, False],
        "with_protoc": [True, False]
    }
    default_options = {
        "fPIC": True,
        "with_proto3": True,
        "with_protoc": True
    }

    def export_sources(self):
        # https://github.com/protobuf-c/protobuf-c/pull/555
        copy(self, "protobuf-c.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("protobuf/[>=3.21.12]")

    def validate(self):
        check_min_cppstd(self, 14)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.19 <5]")
        self.tool_requires("protobuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "build-cmake/CMakeLists.txt", "set(CMAKE_MSVC_RUNTIME_LIBRARY", "# ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_PROTO3"] = self.options.with_proto3
        tc.cache_variables["BUILD_PROTOC"] = self.options.with_protoc
        tc.cache_variables["BUILD_TESTS"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="build-cmake")
        cmake.build()

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "protobuf-c")

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        copy(self, "protobuf-c.cmake", self.source_folder, os.path.join(self.package_folder, self._cmake_install_base_path))

    def package_info(self):
        # upstream CMake config file name and target name matches the package name
        self.cpp_info.libs = ["protobuf-c"]
        self.cpp_info.builddirs.append(self._cmake_install_base_path)
        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_install_base_path, "protobuf-c.cmake")])

        libcxx = stdcpp_library(self)
        if libcxx:
            self.cpp_info.system_libs.append(libcxx)
