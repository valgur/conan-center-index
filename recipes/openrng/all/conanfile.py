import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class OpenRNGConan(ConanFile):
    name = "openrng"
    description = "OpenRNG is an open-source Random Number Generator library developed at Arm."
    license = "MIT"
    homepage = "https://gitlab.arm.com/libraries/openrng"
    topics = ("rng", "random-number-generator")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "interface": ["lp64", "ilp64"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "interface": "lp64",
    }
    implements = ["auto_shared_fpic"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.compiler == "intel-cc":
            # Match MKL's default interface
            self.options.interface = "ilp64"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 20)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_BENCH"] = False
        tc.cache_variables["BUILD_DOCS"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # No CMake config or .pc files are installed by the project
        self.cpp_info.libs = ["openrng"]
        if self.options.interface == "ilp64":
            self.cpp_info.defines.append("OPENRNG_ILP64")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
