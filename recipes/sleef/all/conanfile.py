import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.4"


class SleefConan(ConanFile):
    name = "sleef"
    description = "SLEEF is a library that implements vectorized versions of C standard math functions."
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sleef.org"
    topics = ("vectorization", "simd")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "openmp": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.openmp:
            self.requires("openmp/system")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("shared sleef not supported on Windows, it produces runtime errors")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if not can_run(self):
            self.tool_requires(f"sleef/{self.version}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["sleef"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["tlfloat"], strip_root=True, destination="tlfloat")
        apply_conandata_patches(self)
        # Overridden by CMakeToolchain
        replace_in_file(self, "Configure.cmake", "set(TLFLOAT_SOURCE_DIR ", "# set(TLFLOAT_SOURCE_DIR ")
        replace_in_file(self, "Configure.cmake", "set(TLFLOAT_CMAKE_ARGS ", "set(TLFLOAT_CMAKE_ARGS ${TLFLOAT_CMAKE_ARGS} ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SLEEF_BUILD_STATIC_TEST_BINS"] = False
        tc.cache_variables["SLEEF_BUILD_LIBM"] = True
        tc.cache_variables["SLEEF_BUILD_DFT"] = False
        tc.cache_variables["SLEEF_BUILD_QUAD"] = False
        tc.cache_variables["SLEEF_BUILD_GNUABI_LIBS"] = False
        tc.cache_variables["SLEEF_BUILD_SCALAR_LIB"] = False
        tc.cache_variables["SLEEF_BUILD_TESTS"] = False
        tc.cache_variables["SLEEF_BUILD_INLINE_HEADERS"] = False
        tc.cache_variables["SLEEF_SHOW_CONFIG"] = True
        tc.cache_variables["SLEEF_SHOW_ERROR_LOG"] = False
        tc.cache_variables["SLEEF_ENABLE_ALTDIV"] = False
        tc.cache_variables["SLEEF_ENABLE_ALTSQRT"] = False
        tc.cache_variables["SLEEF_DISABLE_FFTW"] = True
        tc.cache_variables["SLEEF_DISABLE_MPFR"] = True
        tc.cache_variables["SLEEF_DISABLE_SSL"] = True
        tc.cache_variables["SLEEF_ENFORCE_SSE2"] = self.settings.arch in ["x86", "x86_64"]
        tc.cache_variables["SLEEF_ENABLE_CUDA"] = False  # Only used in tests
        tc.cache_variables["SLEEF_ENABLE_OPENMP"] = self.options.openmp
        tc.cache_variables["SLEEF_DISABLE_OPENMP"] = not self.options.openmp
        tc.cache_variables["SLEEF_ENFORCE_OPENMP"] = self.options.openmp
        if "llvm-openmp" in self.dependencies:
            tc.cache_variables["COMPILER_SUPPORTS_OPENMP"] = True
            tc.cache_variables["COMPILER_SUPPORTS_OMP_SIMD"] = True
        if not can_run(self):
            tc.cache_variables["NATIVE_BUILD_DIR"] = self.dependencies.build["sleef"].package_folder.replace("\\", "/")
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["TLFLOAT_SOURCE_DIR"] = "tlfloat"
        if self.options.get_safe("fPIC", True):
            tc.cache_variables["TLFLOAT_CMAKE_ARGS"] = "-DCMAKE_POSITION_INDEPENDENT_CODE=ON"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        if self.settings_target is not None:
            # Building for tool_requires() in cross-compilation. Copy build utils.
            copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "sleef")
        self.cpp_info.set_property("cmake_target_name", "sleef::sleef")
        self.cpp_info.set_property("pkg_config_name", "sleef")
        self.cpp_info.libs = ["sleef"]
        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.defines = ["SLEEF_STATIC_LIBS"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
