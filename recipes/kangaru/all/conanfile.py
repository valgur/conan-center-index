from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
import os

required_conan_version = ">=1.52.0"


class KangaruConan(ConanFile):
    name = "kangaru"
    description = "A dependency injection container for C++11, C++14 and later"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/gracicot/kangaru/wiki"
    topics = ("DI", "IoC", "inversion of control", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "reverse_destruction": [True, False],
        "no_exception": [True, False],
    }
    default_options = {
        "reverse_destruction": True,
        "no_exception": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.settings.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["KANGARU_REVERSE_DESTRUCTION"] = self.options.reverse_destruction
        tc.variables["KANGARU_NO_EXCEPTION"] = self.options.no_exception
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "kangaru")
        self.cpp_info.set_property("cmake_target_name", "kangaru")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
