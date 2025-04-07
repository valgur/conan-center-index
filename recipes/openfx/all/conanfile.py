import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=2.1"


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
        copy(self, "*",
             src=os.path.join(self.recipe_folder, "cmake"),
             dst=os.path.join(self.export_sources_folder, "cmake"))
        copy(self, "*",
             src=os.path.join(self.recipe_folder, "symbols"),
             dst=os.path.join(self.export_sources_folder, "symbols"))

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
        self.requires("expat/[>=2.6.2 <3]")

    def validate(self):
        check_min_cppstd(self, 11)

        # https://github.com/AcademySoftwareFoundation/openfx/blob/OFX_Release_1.5/HostSupport/include/ofxhBinary.h#L9-L24
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.settings.arch not in ["x86", "x86_64"]:
                raise ConanInvalidConfiguration(f"{self.settings.arch} {self.settings.os} is not supported")
        elif self.settings.os != "Windows" and not is_apple_os(self):
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=Path(self.source_folder).parent)
        cmake.build()

    @property
    def _build_modules(self):
        return [os.path.join("lib", "cmake", "OpenFX.cmake")]

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(self, "*.symbols",
             src=os.path.join(self.export_sources_folder, "symbols"),
             dst=os.path.join(self.package_folder, "lib", "symbols"))
        copy(self, "*.cmake",
             src=os.path.join(self.export_sources_folder, "cmake"),
             dst=os.path.join(self.package_folder, "lib", "cmake"))
        copy(self, "LICENSE",
             src=os.path.join(self.source_folder, "Support"),
             dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "openfx")
        self.cpp_info.set_property("cmake_target_name", "openfx::openfx")
        self.cpp_info.set_property("cmake_build_modules", self._build_modules)
        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))

        if self.options.shared:
            self.cpp_info.libs = ["OfxSupport"]
        else:
            self.cpp_info.libs = ["OfxHost", "OfxSupport"]

        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs.extend(["GL"])
        if is_apple_os(self):
            self.cpp_info.frameworks = ["CoreFoundation", "OpenGL"]
