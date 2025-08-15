import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RapidsLoggerConan(ConanFile):
    name = "rapids_logger"
    description = "A logging interface for RAPIDS built on spdlog"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/rapids-logger"
    topics = ("nvidia", "rapids", "logging")
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
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("spdlog/[^1.14]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "  rapids_cpm_spdlog(",
                        "  find_package(spdlog REQUIRED CONFIG)\n"
                        '  message(TRACE "rapids_cpm_spdlog()"')
        replace_in_file(self, "CMakeLists.txt", "set_target_properties(spdlog ", "# ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTS"] = False
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
        rm(self, "rapids_logger-*.cmake", os.path.join(self.package_folder, "lib", "cmake", "rapids_logger"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "rapids_logger")
        self.cpp_info.set_property("cmake_target_name", "rapids_logger::rapids_logger")
        self.cpp_info.libs = ["rapids_logger"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        self.cpp_info.builddirs = ["lib/cmake/rapids_logger"]
        self.cpp_info.set_property("cmake_build_modules", ["lib/cmake/rapids_logger/create_logger_macros.cmake"])
