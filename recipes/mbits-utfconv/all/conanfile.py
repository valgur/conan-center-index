from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import check_min_vs, is_msvc
from conan.tools.files import *
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os


required_conan_version = ">=2.1"


class MBitsUtfConvConan(ConanFile):
    name = "mbits-utfconv"
    description = "Conversion library between string, u16string, u32string and u8string."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mbits-libs/utfconv"
    topics = ("utf-conversion", "utf", "conversion", "utfconv")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("mbits-semver/[^0.1.1]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        path = Path(self.source_folder, "src", "utf.cpp")
        path.write_text("#include <cstdint>\n" + path.read_text())

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["UTFCONV_TESTING"] = False
        tc.variables["UTFCONV_INSTALL"] = True
        tc.variables["UTFCONV_BUILD_AS_STANDALONE"] = True
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mbits-utfconv")
        self.cpp_info.set_property("cmake_target_name", "mbits::utfconv")
        self.cpp_info.libs = ["utfconv"]
