import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.4"


class KissfftConan(ConanFile):
    name = "kissfft"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mborgerding/kissfft"
    description = "a Fast Fourier Transform (FFT) library that tries to Keep it Simple, Stupid"
    topics = ("fft", "kiss", "frequency-domain", "fast-fourier-transform")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "datatype": ["float", "double", "int16_t", "int32_t", "simd"],
        "openmp": [True, False],
        "use_alloca": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "datatype": "float",
        "openmp": True,
        "use_alloca": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.openmp:
            # Used only in kiss_fft.c, not in public headers
            self.requires("openmp/system")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["KISSFFT_PKGCONFIG"] = False
        tc.variables["KISSFFT_STATIC"] = not self.options.shared
        tc.variables["KISSFFT_TEST"] = False
        tc.variables["KISSFFT_TOOLS"] = False
        tc.variables["KISSFFT_DATATYPE"] = self.options.datatype
        tc.variables["KISSFFT_OPENMP"] = self.options.openmp
        tc.variables["KISSFFT_USE_ALLOCA"] = self.options.use_alloca
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        lib_name = "kissfft-{datatype}{openmp}".format(
            datatype=self.options.datatype,
            openmp="-openmp" if self.options.openmp else "",
        )

        self.cpp_info.set_property("cmake_file_name", "kissfft")
        self.cpp_info.set_property("cmake_target_name", "kissfft::kissfft")
        self.cpp_info.set_property("cmake_target_aliases", [f"kissfft::{lib_name}"])
        self.cpp_info.set_property("pkg_config_name", lib_name)
        self.cpp_info.includedirs.append(os.path.join("include", "kissfft"))
        self.cpp_info.libs = [lib_name]

        # got to duplicate the logic from kissfft/CMakeLists.txt
        if self.options.datatype in ["float", "double"]:
            self.cpp_info.defines.append(f"kiss_fft_scalar={self.options.datatype}")
        elif self.options.datatype == "int16_t":
            self.cpp_info.defines.append("FIXED_POINT=16")
        elif self.options.datatype == "int32_t":
            self.cpp_info.defines.append("FIXED_POINT=32")
        elif self.options.datatype == "simd":
            self.cpp_info.defines.append("USE_SIMD")
        if self.options.use_alloca:
            self.cpp_info.defines.append("KISS_FFT_USE_ALLOCA")
        if self.options.shared:
            self.cpp_info.defines.append("KISS_FFT_SHARED")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if self.options.openmp:
            self.cpp_info.requires = ["openmp::openmp"]
