# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, download, export_conandata_patches, get

required_conan_version = ">=1.53.0"


class RectangleBinPackConan(ConanFile):
    name = "rectanglebinpack"
    description = (
        "The code can be used to solve the problem of packing a set of 2D rectangles into a larger bin."
    )
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/juj/RectangleBinPack"
    topics = ("rectangle", "packing", "bin")

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

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version][0], strip_root=True)
        download(self, filename="LICENSE", **self.conan_data["sources"][self.version][1])

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", dst=os.path.join("include", self.name), src=self.source_folder, excludes="old/**")
        copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.a", dst=os.path.join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["RectangleBinPack"]
        self.cpp_info.set_property("cmake_file_name", "RectangleBinPack")
        self.cpp_info.set_property("cmake_target_name", "RectangleBinPack")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "RectangleBinPack"
        self.cpp_info.names["cmake_find_package_multi"] = "RectangleBinPack"
