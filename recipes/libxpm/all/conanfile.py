import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import copy, get

required_conan_version = ">=1.53.0"


class LibXpmConan(ConanFile):
    name = "libxpm"
    description = "X Pixmap (XPM) image file format library"
    license = "MIT-open-group"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/lib/libxpm"
    topics = ("xorg", "x11", "xpm")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_xorg_system": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_xorg_system": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os == "Windows" or is_apple_os(self):
            del self.options.use_xorg_system

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os != "Windows":
            if self.options.use_xorg_system:
                self.requires("xorg/system")
            else:
                self.requires("libx11/1.8.10")

    def validate(self):
        if self.settings.os not in ("Windows", "Linux", "FreeBSD"):
            raise ConanInvalidConfiguration("libXpm is supported only on Windows, Linux and FreeBSD")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CONAN_libXpm_VERSION"] = self.version
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        deps = CMakeDeps(self)
        deps.generate()

    def package(self):
        copy(self, "COPYING",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "COPYRIGHT",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "xpm")
        self.cpp_info.set_property("cmake_target_aliases", ["X11::Xpm"])
        self.cpp_info.libs = ["Xpm"]
        if self.settings.os == "Windows":
            self.cpp_info.defines = ["FOR_MSW"]
        else:
            if self.options.use_xorg_system:
                self.cpp_info.requires = ["xorg::x11"]
            else:
                self.cpp_info.requires = ["libx11::libx11"]
