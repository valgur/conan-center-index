from conan import ConanFile
from conan.tools.microsoft import is_msvc
from conan.tools.files import export_conandata_patches, get, copy, rmdir
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
import os


required_conan_version = ">=2.1"


class WildmidiConan(ConanFile):
    name = "wildmidi"
    description = "WildMIDI is a simple software midi player which has a core softsynth library that can be used in other applications."
    license = "LGPL-3.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.mindwerks.net/projects/wildmidi"
    topics = ("audio", "midi", "multimedia", "music", "softsynth", "sound", "synth")
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
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.settings.os == "Windows":
            tc.variables["CMAKE_BUILD_TYPE"] = self.settings.build_type
        tc.variables["WANT_PLAYER"] = False
        if not self.options.shared:
            tc.variables["WANT_STATIC"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="docs/license/LGPLv3.txt", dst=os.path.join(
            self.package_folder, "licenses"), src=self.source_folder, keep_path=False)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        if is_msvc(self):
            libname = "libWildMidi"
            if not self.options.shared:
                libname += "-static"
        else:
            libname = "WildMidi"

        self.cpp_info.set_property("cmake_file_name", "WildMidi")
        self.cpp_info.set_property("cmake_target_name", "WildMidi::libwildmidi")
        self.cpp_info.set_property("pkg_config_name", "wildmidi")

        self.cpp_info.libs = [libname]
        if not self.options.shared:
            self.cpp_info.defines = ["WILDMIDI_STATIC"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
