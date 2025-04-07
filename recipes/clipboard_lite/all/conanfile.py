import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy, export_conandata_patches, apply_conandata_patches, replace_in_file

required_conan_version = ">=2.1"

class ClipboardLiteConan(ConanFile):
    name = "clipboard_lite"
    description = "cross platform clipboard library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/smasherprog/clipboard_lite"
    topics = ("clipboard")
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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("xorg/system")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Add X11 as targets, since include dir vars don't propagate deps
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "find_package(X11 REQUIRED)",
                        "find_package(X11 REQUIRED)\n"
                        "link_libraries(X11::xcb X11::X11 X11::Xfixes)\n")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["clipboard_lite"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.requires.extend(["xorg::xcb", "xorg::x11", "xorg::xfixes"])
            self.cpp_info.system_libs.extend(["m", "pthread"])
        elif is_apple_os(self):
            self.cpp_info.frameworks = ["Cocoa", "Carbon", "CoreFoundation", "CoreGraphics", "Foundation", "AppKit"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs.extend([
                "shlwapi",
                "windowscodecs",
            ])
