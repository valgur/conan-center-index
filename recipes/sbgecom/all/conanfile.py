import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, check_min_cstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class SbgEComConan(ConanFile):
    name = "sbgecom"
    description = "sbgECom is a C library used to communicate with SBG Systems IMU, AHRS and INS"
    license = "MIT"
    homepage = "https://github.com/SBG-Systems/sbgECom"
    topics = ("sbg", "imu", "ahrs", "ins")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
    }
    implements = ["auto_shared_fpic"]

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.tools:
            self.languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.tools:
            self.requires("argtable3/[>=3.1.5 <4]")

    def validate(self):
        check_min_cppstd(self, 14)
        if self.settings.compiler.get_safe("cstd"):
            check_min_cstd(self, 99)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Let Conan handle cxxstd, cstd and fPIC
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 14)", "")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_C_STANDARD 99)", "")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        # Add unofficial shared build support
        replace_in_file(self, "CMakeLists.txt",
                        "add_library(${PROJECT_NAME} STATIC)",
                        "add_library(${PROJECT_NAME})")
        # Get argtable3 from Conan
        replace_in_file(self, "CMakeLists.txt",
                        "if (BUILD_EXAMPLES OR BUILD_TOOLS)",
                        "if (BUILD_EXAMPLES OR BUILD_TOOLS)\n"
                        "  find_package(Argtable3 REQUIRED)\n"
                        "endif()\n"
                        "if(FALSE)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_TOOLS"] = self.options.tools
        tc.cache_variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "sbgECom")
        self.cpp_info.set_property("cmake_target_name", "sbgECom::sbgECom")
        self.cpp_info.libs = ["sbgECom"]
        if not self.options.shared:
            self.cpp_info.defines = ["SBG_COMMON_STATIC_USE"]
        if self.settings.compiler == "msvc":
            self.cpp_info.system_libs = ["ws2_32"]
