import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class PortAudioRecipe(ConanFile):
    name = "portaudio"
    description = "PortAudio is a cross-platform, open-source C language library for real-time audio input and output."
    license = "MIT"
    topics = ("audio",)
    homepage = "http://www.portaudio.com"

    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_alsa": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_alsa": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_alsa

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("with_alsa", False):
            self.requires("libalsa/[~1.2.10]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 support
        if Version(self.version) <= "19.7":
            replace_in_file(self, "CMakeLists.txt",
                            "CMAKE_MINIMUM_REQUIRED(VERSION 2.8)",
                            "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["PA_BUILD_STATIC"] = not self.options.shared
        tc.cache_variables["PA_BUILD_SHARED"] = self.options.shared
        tc.cache_variables["PA_LIBNAME_ADD_SUFFIX"] = False
        tc.cache_variables["PA_USE_ALSA"] = self.options.get_safe("with_alsa", False)
        tc.cache_variables["PA_USE_JACK"] = False  # Jack is not available as a Conan package
        tc.cache_variables["PA_USE_ASIO"] = False  # ASIO SDK is not available as a Conan package
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", os.path.join(self.source_folder), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "portaudio")
        self.cpp_info.set_property("cmake_target_name", "portaudio")
        if not self.options.shared:
            self.cpp_info.set_property("cmake_target_aliases", ["portaudio_static"])
        self.cpp_info.set_property("pkg_config_name", "portaudio-2.0")

        self.cpp_info.libs = ["portaudio"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
        elif is_msvc(self):
            self.cpp_info.system_libs = ["winmm", "dsound", "ole32", "uuid", "setupapi"]
        elif is_apple_os(self):
            self.cpp_info.frameworks = ["CoreAudio", "AudioToolbox", "AudioUnit", "CoreFoundation", "CoreServices"]
