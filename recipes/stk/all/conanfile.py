import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class StkConan(ConanFile):
    name = "stk"
    description = ("The Synthesis ToolKit in C++ (STK) is a set of open source audio signal processing "
                   "and algorithmic synthesis classes written in the C++ programming language.")
    license = "X11-distribute-modifications-variant"
    homepage = "https://github.com/thestk/stk"
    topics = ("audio", "signal-processing", "audio-synthesis")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "install_data": [True, False],
        "with_alsa": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "install_data": True,
        "with_alsa": True,
    }
    implements = ["auto_shared_fpic"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_alsa

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("with_alsa"):
            self.requires("libalsa/[~1.2.10]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.os in ["Linux", "FreeBSD"] and not self.options.with_alsa:
            # Compilation fails if ALSA is disabled.
            # Might be possible to use Jack instead, but it's not available as a Conan package.
            raise ConanInvalidConfiguration("ALSA cannot be disabled")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.5)")
        replace_in_file(self, "CMakeLists.txt", "set (CMAKE_CXX_STANDARD 11)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["COMPILE_PROJECTS"] = False  # disable samples
        tc.cache_variables["BUILD_SHARED"] = self.options.shared
        tc.cache_variables["BUILD_STATIC"] = not self.options.shared
        tc.cache_variables["ENABLE_ALSA"] = self.options.get_safe("with_alsa", False)
        tc.cache_variables["ENABLE_JACK"] = False  # Jack is not available as a Conan package
        tc.cache_variables["ENABLE_ASIO"] = False  # ASIO SDK is not available as a Conan package
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

        if self.options.install_data:
            copy(self, "*.raw",
                 os.path.join(self.source_folder, "rawwaves"),
                 os.path.join(self.package_folder, "share", "stk", "rawwaves"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "stk")
        self.cpp_info.set_property("cmake_target_name", "stk")
        if self.options.shared:
            self.cpp_info.set_property("cmake_target_aliases", ["stk_SHARED"])

        self.cpp_info.libs = ["stk"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["winmm", "ole32", "wsock32", "mfuuid", "mfplat", "wmcodecdspuuid", "ksuser", "dsound"]
        elif is_apple_os(self):
            self.cpp_info.frameworks = ["CoreAudio", "CoreFoundation", "CoreMIDI"]

        if self.options.install_data:
            # Not an official env var
            self.runenv_info.define_path("STK_RAWWAVE_PATH", os.path.join(self.package_folder, "share", "stk", "rawwaves"))
