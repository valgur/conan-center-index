from conan import ConanFile
from conan.tools.files import get, copy, export_conandata_patches, apply_conandata_patches
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os

required_conan_version = ">=1.53.0"


class KaitaiStructCppStlRuntimeConan(ConanFile):
    name = "kaitai_struct_cpp_stl_runtime"
    description = "kaitai struct c++ runtime library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://kaitai.io/"
    topics = ("parsers", "streams", "dsl", "kaitai struct")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "with_iconv": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zlib": False,
        "with_iconv": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.13")
        if self.options.with_iconv:
            self.requires("libiconv/1.17")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"
        if self.options.with_iconv:
            tc.variables["STRING_ENCODING_TYPE"] = "ICONV"
        else:
            tc.variables["STRING_ENCODING_TYPE"] = "NONE"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["kaitai_struct_cpp_stl_runtime"]
