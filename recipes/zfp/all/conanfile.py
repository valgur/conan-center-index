from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import copy, get, rmdir, replace_in_file
from conan.tools.scm import Version
import os

required_conan_version = ">=2.1"


class ZfpConan(ConanFile):
    name = "zfp"
    description = "Compressed numerical arrays that support high-speed random access"
    homepage = "https://github.com/LLNL/zfp"
    url = "https://github.com/conan-io/conan-center-index"
    license = "BSD-3-Clause"
    topics = ("compression", "arrays")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "bit_stream_word_size": [8,16,32,64],
        "with_cuda": [True, False],
        "with_bit_stream_strided": [True, False],
        "with_aligned_alloc": [True, False],
        "with_cache_twoway": [True, False],
        "with_cache_fast_hash": [True, False],
        "with_cache_profile": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "bit_stream_word_size": 64,
        "with_cuda": False,
        "with_bit_stream_strided": False,
        "with_aligned_alloc": False,
        "with_cache_twoway": False,
        "with_cache_fast_hash": False,
        "with_cache_profile": False,
        "with_openmp": True,
    }

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
            # https://github.com/LLNL/zfp/blob/1.0.1/include/zfp/internal/array/store.hpp#L130
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.options.with_cuda:
            self.output.warning("Conan package for CUDA is not available, this package will be used from system.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_CFP"] = True
        tc.variables["BUILD_UTILITIES"] = False
        tc.variables["ZFP_WITH_CUDA"] = self.options.with_cuda
        tc.variables["ZFP_BIT_STREAM_WORD_SIZE"] = self.options.bit_stream_word_size
        tc.variables["ZFP_WITH_BIT_STREAM_STRIDED"] = self.options.with_bit_stream_strided
        tc.variables["ZFP_WITH_ALIGNED_ALLOC"] = self.options.with_aligned_alloc
        tc.variables["ZFP_WITH_CACHE_TWOWAY"] = self.options.with_cache_twoway
        tc.variables["ZFP_WITH_CACHE_FAST_HASH"] = self.options.with_cache_fast_hash
        tc.variables["ZFP_WITH_CACHE_PROFILE"] = self.options.with_cache_profile
        tc.variables["ZFP_WITH_CUDA"] = self.options.with_cuda
        tc.variables["ZFP_WITH_OPENMP"] = self.options.with_openmp
        if self.settings.os != "Windows" and not self.options.shared:
            tc.variables["ZFP_ENABLE_PIC"] = self.options.fPIC
        tc.variables["BUILD_TESTING"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        if Version(self.version) < "1.0":
            replace_in_file(self, os.path.join(self.source_folder, "src", "CMakeLists.txt"),
                            "target_compile_options(zfp PRIVATE ${OpenMP_C_FLAGS})", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zfp")
        # to avoid to create an unwanted target, since we can't allow zfp::zfp to be the global target here
        self.cpp_info.set_property("cmake_target_name", "zfp::cfp")

        # zfp
        self.cpp_info.components["_zfp"].set_property("cmake_target_name", "zfp::zfp")
        self.cpp_info.components["_zfp"].libs = ["zfp"]

        # cfp
        self.cpp_info.components["cfp"].set_property("cmake_target_name", "zfp::cfp")
        self.cpp_info.components["cfp"].libs = ["cfp"]
        self.cpp_info.components["cfp"].requires = ["_zfp"]

        if self.options.with_openmp:
            self.cpp_info.components["_zfp"].requires.append("openmp::openmp")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_zfp"].system_libs.append("m")
