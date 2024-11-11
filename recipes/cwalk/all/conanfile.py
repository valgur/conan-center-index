import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class CwalkConan(ConanFile):
    name = "cwalk"
    description = "Path library for C/C++. Cross-Platform for Windows, " \
                  "MacOS and Linux. Supports UNIX and Windows path styles " \
                  "on those platforms."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://likle.github.io/cwalk/"
    topics = ("cross-platform", "windows", "macos", "osx", "linux",
              "path-manipulation", "path", "directory", "file", "file-system",
              "unc", "path-parsing", "file-path")
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
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Cwalk")
        self.cpp_info.set_property("cmake_target_name", "cwalk")
        self.cpp_info.libs = ["cwalk"]
        if self.options.shared and Version(self.version) >= "1.2.5":
            self.cpp_info.defines.append("CWK_SHARED")
        if Version(self.version) >= "1.2.8":
            self.cpp_info.set_property("pkg_config_name", "cwalk")
