# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.53.0"


class openfx(ConanFile):
    name = "openfx"
    description = "OpenFX image processing plug-in standard."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://openeffects.org"
    topics = ("image-processing", "standard")

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
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "cmake", src=self.recipe_folder, dst=self.export_sources_folder)
        copy(self, "symbols", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opengl/system")
        self.requires("expat/2.4.8")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination="source_subfolder", strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _build_modules(self):
        return [os.path.join("lib", "cmake", "OpenFX.cmake")]

    def package(self):
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        copy(self, "*.symbols", src="symbols", dst=os.path.join(self.package_folder, "lib/symbols"))
        copy(self, "*.cmake", src="cmake", dst=os.path.join(self.package_folder, "lib/cmake"))
        copy(
            self, "LICENSE", src="source_subfolder/Support", dst=os.path.join(self.package_folder, "licenses")
        )
        copy(self, "readme.md")

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "openfx"
        self.cpp_info.names["cmake_find_package_multi"] = "openfx"

        self.cpp_info.set_property("cmake_build_modules", self._build_modules)
        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))
        self.cpp_info.build_modules["cmake_find_package"] = self._build_modules
        self.cpp_info.build_modules["cmake_find_package_multi"] = self._build_modules

        if self.options.shared:
            self.cpp_info.libs = ["OfxSupport"]
        else:
            self.cpp_info.libs = ["OfxHost", "OfxSupport"]

        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs.extend(["GL"])
        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "OpenGL"]
