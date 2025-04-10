import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class Chipmunk2DConan(ConanFile):
    name = "chipmunk2d"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://chipmunk-physics.net"
    topics = ("physics", "engine", "game development")
    description = "Chipmunk2D is a simple, lightweight, fast and portable 2D "\
                  "rigid body physics library written in C."

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # The finite-math-only optimization has no effect and can cause linking errors
        # when linked against glibc >= 2.31
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "-ffast-math", "-ffast-math -fno-finite-math-only")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_DEMOS"] = False
        tc.variables["INSTALL_DEMOS"] = False
        tc.variables["INSTALL_STATIC"] = not self.options.shared
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

    def export_sources(self):
        export_conandata_patches(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["chipmunk"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
