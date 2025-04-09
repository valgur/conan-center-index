import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class ZenohCppConan(ConanFile):
    name = "zenoh-cpp"
    description = "C++ API for Zenoh"
    license = "Apache-2.0 OR EPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/eclipse-zenoh/zenoh-cpp"
    topics = ("networking", "pub-sub", "messaging", "robotics", "ros2", "iot", "edge-computing", "micro-controllers")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "backend": [None, "c", "pico"],
    }
    default_options = {
        "backend": "c",
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.backend == "c":
            self.requires(f"zenoh-c/{self.version}")
        elif self.options.backend == "pico":
            self.requires(f"zenoh-pico/{self.version}")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[^4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ZENOHCXX_ZENOHC"] = self.options.backend == "c"
        tc.cache_variables["ZENOHCXX_ZENOHPICO"] = self.options.backend == "pico"
        tc.cache_variables["ZENOHCXX_EXAMPLES_PROTOBUF"] = False
        tc.cache_variables["ZENOHCXX_ENABLE_TESTS"] = False
        tc.cache_variables["ZENOHCXX_ENABLE_EXAMPLES"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zenohcxx")
        self.cpp_info.set_property("pkg_config_name", "zenohcxx")

        if self.options.backend == "c":
            self.cpp_info.components["zenohc"].set_property("cmake_target_name", "zenohcxx::zenohc")
            self.cpp_info.components["zenohc"].bindirs = []
            self.cpp_info.components["zenohc"].libdirs = []
            self.cpp_info.components["zenohc"].requires = ["zenoh-c::zenoh-c"]
            self.cpp_info.components["zenohc"].defines = ["ZENOHCXX_ZENOHC"]
        elif self.options.backend == "pico":
            self.cpp_info.components["zenohpico"].set_property("cmake_target_name", "zenohcxx::zenohpico")
            self.cpp_info.components["zenohpico"].bindirs = []
            self.cpp_info.components["zenohpico"].libdirs = []
            self.cpp_info.components["zenohpico"].requires = ["zenoh-pico::zenoh-pico"]
            self.cpp_info.components["zenohpico"].defines = ["ZENOHCXX_ZENOHPICO"]
