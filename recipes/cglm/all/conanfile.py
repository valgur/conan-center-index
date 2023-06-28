# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, get, rmdir

required_conan_version = ">=1.53.0"


class CglmConan(ConanFile):
    name = "cglm"
    description = "Highly Optimized Graphics Math (glm) for C "
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/recp/cglm"
    topics = ("graphics", "opengl", "simd", "vector", "glm")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "header_only": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.header_only:
            self.settings.rm_safe("arch")
            self.settings.rm_safe("build_type")
            self.settings.rm_safe("compiler")
            self.settings.rm_safe("os")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CGLM_STATIC"] = not self.options.shared
        tc.variables["CGLM_SHARED"] = self.options.shared
        tc.variables["CGLM_USE_TEST"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        if self.options.header_only:
            copy(
                self,
                "*",
                src=os.path.join(self.source_folder, "include"),
                dst=os.path.join(self.package_folder, "include"),
            )
        else:
            cmake = CMake(self)
            cmake.install()
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cglm")
        self.cpp_info.set_property("cmake_target_name", "cglm::cglm")
        self.cpp_info.set_property("pkg_config_name", "cglm")

        if not self.options.header_only:
            self.cpp_info.libs = ["cglm"]
            if self.settings.os in ("Linux", "FreeBSD"):
                self.cpp_info.system_libs.append("m")

        # backward support of cmake_find_package, cmake_find_package_multi & pkg_config generators
        self.cpp_info.names["cmake_find_package"] = "cglm"
        self.cpp_info.names["cmake_find_package_multi"] = "cglm"
