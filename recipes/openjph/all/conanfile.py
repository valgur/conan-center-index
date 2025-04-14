import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class OpenJPH(ConanFile):
    name = "openjph"
    description = "Open-source implementation of JPEG2000 Part-15 (or JPH or HTJ2K)"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/aous72/OpenJPH"
    topics = ("ht-j2k", "jpeg2000", "jp2", "openjph", "image", "multimedia", "format", "graphics")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_executables": [True, False],
        "with_tiff": [True, False],
        "with_stream_expand_tool": [True, False],
        "disable_simd": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_executables": True,
        "with_tiff": True,
        "with_stream_expand_tool": False,
        "disable_simd": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_executables and self.options.with_tiff:
            self.requires("libtiff/[>=4.5 <5]")

    def validate(self):
        if self.options.with_stream_expand_tool:
            check_min_cppstd(self, 14)
        else:
            check_min_cppstd(self, 11)

        if self.settings.compiler == "gcc" and \
            Version(self.settings.compiler.version) < "6.0":
            raise ConanInvalidConfiguration(f"{self.ref} requires gcc >= 6.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OJPH_BUILD_EXECUTABLES"] = self.options.with_executables
        tc.variables["OJPH_ENABLE_TIFF_SUPPORT"] = self.options.with_tiff
        tc.variables["OJPH_BUILD_STREAM_EXPAND"] = self.options.with_stream_expand_tool
        tc.variables["OJPH_DISABLE_SIMD"] = self.options.disable_simd
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cm = CMake(self)
        cm.configure()
        cm.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        cm = CMake(self)
        cm.install()

        # Cleanup package own pkgconfig
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "openjph")
        self.cpp_info.set_property("cmake_target_name", "openjph::openjph")
        self.cpp_info.set_property("pkg_config_name", "openjph")

        version_suffix = ""
        if is_msvc(self):
            v = Version(self.version)
            version_suffix = f".{v.major}.{v.minor}"
        self.cpp_info.libs = ["openjph" + version_suffix]
