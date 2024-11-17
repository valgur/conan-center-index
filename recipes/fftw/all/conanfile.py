from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir, replace_in_file
import os

required_conan_version = ">=1.54.0"

SINGLE = 'single'
DOUBLE = 'double'
LONGDOUBLE = 'longdouble'
QUAD = 'quad'
ALL = [SINGLE, DOUBLE, LONGDOUBLE, QUAD]


class FFTWConan(ConanFile):
    name = "fftw"
    description = "C subroutine library for computing the Discrete Fourier Transform (DFT) in one or more dimensions"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.fftw.org/"
    license = "GPL-2.0"
    topics = ("fftw", "dft", "dct", "dst")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "precision": ALL + ['deprecated'],
        'precision_single': [True, False],
        'precision_double': [True, False],
        'precision_longdouble': [True, False],
        'precision_quad': [True, False],
        "openmp": [True, False],
        "threads": [True, False],
        "combinedthreads": [True, False],
        "simd": ["sse", "sse2", "avx", "avx2", False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "precision": 'deprecated',
        'precision_single': True,
        'precision_double': True,
        'precision_longdouble': True,
        'precision_quad': False,
        "openmp": True,
        "threads": False,
        "combinedthreads": False,
        "simd": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")
        if not self.options.threads:
            del self.options.combinedthreads
        if self.options.precision != "deprecated":
            self.output.warning("precision options is deprecated! use dedicated options 'precision_single', 'precision_double', 'precision_longdouble' and 'precision_quad' instead")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.openmp:
            self.requires("openmp/system")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            if self.options.openmp:
                raise ConanInvalidConfiguration("Shared fftw with openmp can't be built on Windows")
            if self.options.threads and not self.options.combinedthreads:
                raise ConanInvalidConfiguration("Shared fftw with threads and not combinedthreads can't be built on Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["ENABLE_OPENMP"] = self.options.openmp
        tc.variables["ENABLE_THREADS"] = self.options.threads
        tc.variables["WITH_COMBINED_THREADS"] = self.options.get_safe("combinedthreads", False)
        tc.variables["ENABLE_SSE"] = self.options.simd == "sse"
        tc.variables["ENABLE_SSE2"] = self.options.simd == "sse2"
        tc.variables["ENABLE_AVX"] = self.options.simd == "avx"
        tc.variables["ENABLE_AVX2"] = self.options.simd == "avx2"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    @property
    def _all_precisions(self):
        return [p for p in ALL if self.options.get_safe(f"precision_{p}")]

    def _patch_sources(self):
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "find_package (OpenMP)", "find_package(OpenMP REQUIRED)")
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "target_compile_options (${fftw3_lib}_omp PRIVATE ${OpenMP_C_FLAGS})",
                        "target_link_libraries (${fftw3_lib}_omp OpenMP::OpenMP_C)")

    def build(self):
        def on_off(value):
            return "ON" if value else 'OFF'

        self._patch_sources()
        for current_precision in self._all_precisions:
            cmake = CMake(self)
            variables = {
                "ENABLE_FLOAT": on_off(current_precision == SINGLE),
                "ENABLE_LONG_DOUBLE": on_off(current_precision == LONGDOUBLE),
                "ENABLE_QUAD_PRECISION": on_off(current_precision == QUAD)
            }
            cmake.configure(variables=variables)
            cmake.build()
            cmake.install()

    def package(self):
        copy(self, "COPYRIGHT", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        cmake_config_name = cmake_namespace = "FFTW3"

        self.cpp_info.set_property("cmake_file_name", cmake_config_name)

        for precision in self._all_precisions:
            prec_suffix = self._prec_suffix[precision]
            cmake_target_name = pkgconfig_name = lib_name = "fftw3" + prec_suffix

            if self.options.openmp:
                self.cpp_info.libs.append(lib_name + "_omp")
                self.cpp_info.requires.append("openmp::openmp")
            if self.options.threads and not self.options.combinedthreads:
                self.cpp_info.libs.append(lib_name + "_threads")
            self.cpp_info.libs.append(lib_name)
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs.append("m")
                if precision == QUAD:
                    self.cpp_info.system_libs.extend(["quadmath"])
                    if self.options.threads:
                        self.cpp_info.system_libs.append("pthread")
            self.cpp_info.includedirs.append(os.path.join(self.package_folder, "include"))

            self.cpp_info.set_property("cmake_target_name", f"{cmake_namespace}::{cmake_target_name}")
            self.cpp_info.set_property("pkg_config_name", pkgconfig_name)

    def package_id(self):
        del self.info.options.precision

    @property
    def _prec_suffix(self):
        return {
            "double": "",
            "single": "f",
            "longdouble": "l",
            'quad': 'q'
        }
