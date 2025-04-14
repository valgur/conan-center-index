import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class OnigurumaConan(ConanFile):
    name = "oniguruma"
    description = "Oniguruma is a modern and flexible regular expressions library."
    license = "BSD-2-Clause"
    topics = ("oniguruma", "regex")
    homepage = "https://github.com/kkos/oniguruma"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "posix_api": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "posix_api": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_POSIX_API"] = self.options.posix_api
        tc.variables["ENABLE_BINARY_COMPATIBLE_POSIX_API"] = self.options.posix_api
        if Version(self.version) >= "6.9.8":
            tc.variables["INSTALL_DOCUMENTATION"] = False
            tc.variables["INSTALL_EXAMPLES"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if Version(self.version) < "6.9.8":
            rmdir(self, os.path.join(self.package_folder, "share"))
        else:
            if self.settings.os == "Windows" and self.options.shared:
                rm(self, "onig-config", os.path.join(self.package_folder, "bin"))
            else:
                rmdir(self, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "oniguruma")
        self.cpp_info.set_property("cmake_target_name", "oniguruma::onig")
        self.cpp_info.set_property("pkg_config_name", "oniguruma")
        self.cpp_info.libs = ["onig"]
        if not self.options.shared:
            self.cpp_info.defines.append("ONIG_STATIC")
