import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import collect_libs, copy, get
from conan.tools.gnu import PkgConfigDeps

required_conan_version = ">=1.53.0"


class libuiConan(ConanFile):
    name = "libui"
    description = "Simple and portable GUI library in C that uses the native GUI technologies of each platform it supports."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/andlabs/libui"
    topics = ("ui", "gui")

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
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            # GTK 4 is not yet supported
            self.requires("gtk/3.24.43")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = CMakeToolchain(self)
        tc.generate()
        tc = PkgConfigDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", self.source_folder, os.path.join(self.package_folder, "include"))
        copy(self, "*.dll", self.build_folder, os.path.join(self.package_folder, "bin"), keep_path=False)
        for pattern in ["*.a", "*.so*", "*.dylib*", "*.lib"]:
            copy(self, pattern, self.build_folder, os.path.join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs += ["dl"]
            self.cpp_info.requires = ["gtk::gtk+-3.0"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs += [
                "user32",
                "kernel32",
                "gdi32",
                "comctl32",
                "msimg32",
                "comdlg32",
                "d2d1",
                "dwrite",
                "ole32",
                "oleaut32",
                "oleacc",
                "uuid",
                "windowscodecs",
            ]
