# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get

required_conan_version = ">=1.53.0"


class FlintConan(ConanFile):
    name = "flint"
    description = "FLINT (Fast Library for Number Theory)"
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.flintlib.org"
    topics = ("math", "numerical")

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

    def requirements(self):
        self.requires("gmp/6.2.1")
        self.requires("mpfr/4.1.0")
        if self.settings.compiler == "Visual Studio":
            self.requires("pthreads4w/3.0.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_DOCS"] = False
        tc.variables["WITH_NTL"] = False
        # IPO/LTO breaks clang builds
        tc.variables["IPO_SUPPORTED"] = False
        # No BLAS yet
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_CBLAS"] = True
        # handle run in a cross-build
        if cross_building(self):
            tc.variables["FLINT_USES_POPCNT_EXITCODE"] = "1"
            tc.variables["FLINT_USES_POPCNT_EXITCODE__TRYRUN_OUTPUT"] = ""
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "libflint"
        self.cpp_info.names["cmake_find_package_multi"] = "libflint"

        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["pthread", "m"]

        self.cpp_info.includedirs.append(os.path.join("include", "flint"))
        self.cpp_info.libs = collect_libs(self)
