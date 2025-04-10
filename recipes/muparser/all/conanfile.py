import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MuParserConan(ConanFile):
    name = "muparser"
    license = "BSD-2-Clause"
    homepage = "https://beltoforion.de/en/muparser/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("math", "parser",)
    description = "Fast Math Parser Library"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openmp:
            # Used only in muParserBase.cpp
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_SAMPLES"] = False
        tc.variables["ENABLE_OPENMP"] = self.options.with_openmp
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        license_file = "License.txt" if Version(self.version) < "2.3.3" else "LICENSE"
        copy(self, license_file, src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "muparser")
        self.cpp_info.set_property("cmake_target_name", "muparser::muparser")
        self.cpp_info.set_property("pkg_config_name", "muparser")
        self.cpp_info.libs = ["muparser"]
        if not self.options.shared:
            self.cpp_info.defines = ["MUPARSER_STATIC=1"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs.append("m")
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)
