from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.files import *
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.microsoft import is_msvc
import os


required_conan_version = ">=2.1"


class AudiowaveformConan(ConanFile):
    name = "audiowaveform"
    description = "C++ program to generate waveform data and render waveform images from audio files"
    license = "GPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://waveform.prototyping.bbc.co.uk/"
    topics = ("audio", "c-plus-plus")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        pass

    def configure(self):
        pass

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libgd/2.3.3")
        self.requires("libid3tag/0.16.3")
        self.requires("libmad/0.15.1b")
        self.requires("libsndfile/[^1.2.2]")
        self.requires("boost/1.86.0")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        if is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.ref} cannot be built on Visual Studio and msvc.")

    def build_requirements(self):
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        rm(self, "Find*.cmake", os.path.join(self.source_folder, "CMake"))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_TESTS"] = False
        if not valid_min_cppstd(self, self._min_cppstd):
            tc.variables["CMAKE_CXX_STANDARD"] = self._min_cppstd
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
