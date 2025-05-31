import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class CubicInterpolationConan(ConanFile):
    name = "cubicinterpolation"
    description = "Leightweight interpolation library based on boost and eigen."
    license = "MIT"
    homepage = "https://github.com/MaxSac/cubic_interpolation"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("interpolation", "splines", "cubic", "bicubic", "boost", "eigen3")
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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]", options={
            "with_filesystem": True,
            "with_math": True,
            "with_serialization": True,
        })
        self.requires("eigen/3.4.0")

    def validate(self):
        check_min_cppstd(self, 14)

        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} shared is not supported with Visual Studio")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_EXAMPLE"] = False
        tc.variables["BUILD_DOCUMENTATION"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CubicInterpolation")
        self.cpp_info.set_property("cmake_target_name", "CubicInterpolation::CubicInterpolation")
        self.cpp_info.libs = ["CubicInterpolation"]
        self.cpp_info.requires = ["boost::headers", "boost::filesystem", "boost::math", "boost::serialization", "eigen::eigen"]
