import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get

required_conan_version = ">=2.0.9"


class PiexConan(ConanFile):
    name = "piex"
    description = "short description"
    license = "The Preview Image Extractor (PIEX) is designed to find and extract the largest JPEG compressed preview image contained in a RAW file."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/piex"
    topics = ("raw", "image", "preview", "thumbnail")
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

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.os == "Windows" and self.options.shared:
            # No symbols exported
            raise ConanInvalidConfiguration(f"{self.ref} can not be built as shared on Windows.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
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
        self.cpp_info.libs = [
            "piex",
            "binary_parse",
            "image_type_recognition",
            "tiff_directory",
        ]
        self.cpp_info.includedirs.append(os.path.join("include", "src"))
