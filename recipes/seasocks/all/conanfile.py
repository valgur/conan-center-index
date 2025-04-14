import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class SeasocksConan(ConanFile):
    name = "seasocks"
    description = "A tiny embeddable C++ HTTP and WebSocket server for Linux"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mattgodbolt/seasocks"
    topics = ("embeddable", "webserver", "websockets")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zlib": True,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _min_cppstd(self):
        return 11 if Version(self.version) < "1.4.5" else 17

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/[>=1.2.11 <2]")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration(f"{self.ref} doesn't support this os")
        check_min_cppstd(self, self._min_cppstd)

    def build_requirements(self):
        self.tool_requires("cpython/[~3.12]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # No warnings as errors
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(self, cmakelists, "-Werror", "")
        replace_in_file(self, cmakelists, "-pedantic-errors", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DEFLATE_SUPPORT"] = self.options.with_zlib
        tc.variables["SEASOCKS_SHARED"] = self.options.shared
        tc.variables["SEASOCKS_EXAMPLE_APP"] = False
        tc.variables["UNITTESTS"] = False
        if Version(self.version) < "1.4.6":
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Seasocks")
        self.cpp_info.set_property("cmake_target_name", "Seasocks::seasocks")
        self.cpp_info.libs = ["seasocks"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "m"])
