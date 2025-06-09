import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.4"


class LibYangConan(ConanFile):
    name = "libyang"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    description = "YANG data modeling language library"
    homepage = "https://github.com/CESNET/libyang"
    topics = ("yang", "bsd", "netconf", "restconf", "yin")
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False]}
    default_options = {
        "shared": False,
        "fPIC": True
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def requirements(self):
        self.requires("pcre2/[^10.42]", transitive_headers=True)

    def validate(self):
        # TODO For Windows support: https://github.com/CESNET/libyang?tab=readme-ov-file#windows-build-requirements
        # CMake Error at CMakeLists.txt:386 (find_package):
        #   By not providing "Findpthreads.cmake" in CMAKE_MODULE_PATH this project has
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                f"{self.ref} Conan recipe is not prepared to work on Windows. Contributions are welcome.")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22 <5]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.12)",
                        "cmake_minimum_required(VERSION 3.22.0)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_TESTS"] = False
        tc.variables["ENABLE_VALGRIND_TESTS"] = False
        tc.variables["ENABLE_STATIC"] = not self.options.shared
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LibYANG")
        self.cpp_info.libs = ["yang"]
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "dl", "m"])
