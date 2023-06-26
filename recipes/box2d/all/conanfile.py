import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get

required_conan_version = ">=1.53.0"


class Box2dConan(ConanFile):
    name = "box2d"
    description = "Box2D is a 2D physics engine for games"
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://box2d.org/"
    topics = ("physics", "engine", "game development")

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

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="Box2D")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BOX2D_BUILD_SHARED"] = self.options.shared
        tc.variables["BOX2D_BUILD_STATIC"] = not self.options.shared
        if self.settings.os == "Windows" and self.options.shared:
            tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["BOX2D_BUILD_EXAMPLES"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="Box2D")
        cmake.build()

    def package(self):
        copy(
            self,
            "License.txt",
            src=os.path.join(self.source_folder, "Box2D"),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            os.path.join("Box2D", "*.h"),
            src=os.path.join(self.source_folder, "Box2D"),
            dst=os.path.join(self.package_folder, "include"),
        )
        copy(
            self,
            "*.lib",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "lib"),
            keep_path=False,
        )
        copy(
            self,
            "*.dll",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )
        copy(
            self,
            "*.so*",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "lib"),
            keep_path=False,
        )
        copy(
            self,
            "*.dylib",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "lib"),
            keep_path=False,
        )
        copy(
            self, "*.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False
        )

    def package_info(self):
        self.cpp_info.libs = ["Box2D"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["m"]
