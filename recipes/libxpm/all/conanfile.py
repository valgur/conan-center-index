# TODO: verify the Conan v2 migration

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get

required_conan_version = ">=1.52.0"


class LibXpmConan(ConanFile):
    name = "libxpm"
    description = "X Pixmap (XPM) image file format library"
    license = "MIT-open-group"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/lib/libxpm"
    topics = ("xpm", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    no_copy_source = True

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        if self.settings.os == "Windows":
            copy(self, "windows", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os != "Windows":
            self.requires("xorg/system")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.os not in ("Windows", "Linux", "FreeBSD"):
            raise ConanInvalidConfiguration("libXpm is supported only on Windows, Linux and FreeBSD")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CONAN_libXpm_VERSION"] = self.version
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", "licenses")
        copy(self, "COPYRIGHT", "licenses")
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.libs = ["Xpm"]
        if self.settings.os == "Windows":
            self.cpp_info.defines = ["FOR_MSW"]
