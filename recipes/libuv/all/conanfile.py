import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, check_min_vs

required_conan_version = ">=2.4"


class LibuvConan(ConanFile):
    name = "libuv"
    description = "A multi-platform support library with a focus on asynchronous I/O"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libuv.org"
    topics = ("asynchronous", "io", "networking", "multi-platform")
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
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if is_msvc(self):
            check_min_vs(self, "190")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIBUV_BUILD_TESTS"] = False
        tc.variables["LIBUV_BUILD_SHARED"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        for license_file in ["LICENSE", "LICENSE-docs"]:
            copy(self, license_file, src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    @property
    def _target_name(self):
        return "uv"

    @property
    def _lib_name(self):
        if is_msvc(self) and not self.options.shared:
            return "libuv"
        return "uv"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libuv")
        self.cpp_info.set_property("cmake_target_name", self._target_name)
        self.cpp_info.set_property("pkg_config_name", "libuv" if self.options.shared else "libuv-static")
        self.cpp_info.libs = [self._lib_name]
        if self.options.shared:
            self.cpp_info.defines = ["USING_UV_SHARED=1"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "pthread", "rt"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["iphlpapi", "psapi", "userenv", "ws2_32"]
            self.cpp_info.system_libs.append("dbghelp")
