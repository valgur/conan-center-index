# TODO: verify the Conan v2 migration

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get

required_conan_version = ">=1.53.0"


class WineditlineConan(ConanFile):
    name = "wineditline"
    description = "A BSD-licensed EditLine API implementation for the native Windows Console"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://mingweditline.sourceforge.net/"
    topics = ("readline", "editline", "windows")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Windows":
            message = "wineditline is supported only on Windows."
            raise ConanInvalidConfiguration(message)

    def source(self):
        root = self.source_folder
        get_args = self.conan_data["sources"][self.version]
        get(self, **get_args, destination=root, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", "licenses", self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["edit"]
