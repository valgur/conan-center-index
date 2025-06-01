import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "libinterpolate"
    description = "A C++ interpolation library with a simple interface that supports multiple interpolation methods."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CD3/libInterpolate"
    topics = ("math", "spline", "interpolation", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]", libs=False)
        self.requires("eigen/3.4.0")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os not in ["Linux", "Windows", "Macos"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported.")
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "src"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libInterpolate")
        self.cpp_info.set_property("cmake_target_name", "libInterpolate::Interpolate")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
