import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.0"

class SoundTouchConan(ConanFile):
    name = "soundtouch"
    description = "an open-source audio processing library that allows changing the sound tempo, pitch and playback rate parameters independently"
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://codeberg.org/soundtouch/soundtouch"
    topics = ("audio", "processing", "tempo", "pitch", "playback")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "integer_samples": [True, False],
        "with_openmp": [True, False],
        "with_dll": [True, False],
        "with_util": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "integer_samples": False,
        "with_openmp": True,
        "with_dll": False,
        "with_util": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openmp:
            # not used in any public headers
            self.requires("openmp/system")

    def validate(self):
        if Version(self.version) >= "2.3.3":
            check_min_cppstd(self, 17)

        if self.settings.os == "Macos" and self.options.integer_samples and self.options.with_dll:
            # Undefined symbols for architecture arm64:
            #   "soundtouch::BPMDetect::inputSamples(float const*, int)", referenced from:
            #       _bpm_putSamples in SoundTouchDLL.cpp.o
            #       _bpm_putSamples_i16 in SoundTouchDLL.cpp.o
            raise ConanInvalidConfiguration('The -o="&:integer_samples=True" option is incompatible with -o="&:with_dll=True"')

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)
        apply_conandata_patches(self)
        if Version(self.version) >= "2.3.3":
            # Let Conan handle the C++ standard
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                            "set(CMAKE_CXX_STANDARD 17)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["INTEGER_SAMPLES"] = self.options.integer_samples
        tc.cache_variables["SOUNDTOUCH_DLL"] = self.options.with_dll
        tc.cache_variables["SOUNDSTRETCH"] = self.options.with_util
        tc.cache_variables["OPENMP"] = self.options.with_openmp
        # The finite-math-only optimization has no effect and can cause linking errors
        # when linked against glibc >= 2.31
        tc.blocks["cmake_flags_init"].template = tc.blocks["cmake_flags_init"].template + """
               string(APPEND CMAKE_CXX_FLAGS_INIT " -fno-finite-math-only")
               string(APPEND CMAKE_C_FLAGS_INIT " -fno-finite-math-only")
           """
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING.TXT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SoundTouch")

        self.cpp_info.components["_soundtouch"].set_property("cmake_target_name", "SoundTouch::SoundTouch")
        self.cpp_info.components["_soundtouch"].set_property("pkg_config_name", "soundtouch")
        self.cpp_info.components["_soundtouch"].libs = ["SoundTouch"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_soundtouch"].system_libs.append("m")
        if self.options.with_openmp:
            self.cpp_info.components["_soundtouch"].requires.append("openmp::openmp")

        if self.options.with_dll:
            self.cpp_info.components["SoundTouchDLL"].set_property("cmake_target_name", "SoundTouch::SoundTouchDLL")
            self.cpp_info.components["SoundTouchDLL"].libs = ["SoundTouchDLL"]
            self.cpp_info.components["SoundTouchDLL"].requires = ["_soundtouch"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("mvec")
