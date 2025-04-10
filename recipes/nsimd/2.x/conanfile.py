import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class NsimdConan(ConanFile):
    name = "nsimd"
    description = "Agenium Scale vectorization library for CPUs and GPUs"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/agenium-scale/nsimd"
    topics = ("hpc", "neon", "cuda", "avx", "simd", "avx2", "sse2",
              "aarch64", "avx512", "sse42", "rocm", "sve", "neon128")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # This used only when building the library.
        # Most functionality is header-only.
        "simd": ["cpu", "sse2", "sse42", "avx", "avx2", "avx512_knl",
                 "avx512_skylake", "neon128", "aarch64", "sve", "sve128",
                 "sve256", "sve512", "sve1024", "sve2048", "cuda", "rocm"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "simd": "cpu",
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", " SHARED ", " ")
        replace_in_file(self, "CMakeLists.txt", "RUNTIME DESTINATION lib", "RUNTIME DESTINATION bin")
        replace_in_file(self, "CMakeLists.txt", "set_property(TARGET ${o} PROPERTY POSITION_INDEPENDENT_CODE ON)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["simd"] = self.options.simd
        if self.settings.arch == "armv7hf":
            tc.cache_variables["NSIMD_ARM32_IS_ARMEL"] = False
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = [f"nsimd_{self.options.simd}"]
