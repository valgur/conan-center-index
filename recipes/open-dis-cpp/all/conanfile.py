import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.layout import basic_layout
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class OpenDisConan(ConanFile):
    name = "open-dis-cpp"
    homepage = "https://open-dis.org"
    description = "C++ implementation of the IEEE-1278.1 Distributed Interactive Simulation (DIS) application protocol v6 and v7"
    topics = ("library","protocol","simulation-framework","dis")
    url = "https://github.com/conan-io/conan-center-index"
    license = "BSD-2-Clause"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    def export_sources(self):
        export_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_EXAMPLES"] = "FALSE"
        tc.cache_variables["BUILD_TESTS"] = "FALSE"
        tc.generate()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "res"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_module_file_name", "OpenDIS")
        self.cpp_info.set_property("cmake_file_name", "OpenDIS")
        self.cpp_info.libs = ["OpenDIS6", "OpenDIS7"]
