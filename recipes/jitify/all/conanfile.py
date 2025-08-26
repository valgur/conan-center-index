import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class JitifyConan(ConanFile):
    name = "jitify"
    description = "A single-header C++ library for simplifying the use of CUDA Runtime Compilation (NVRTC)"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVIDIA/jitify"
    topics = ("cuda", "jit", "nvrtc", "header-only")
    package_type = "shared-library"  # the closest to header-only + application
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "header_only": [True, False],
        "v2": [True, False],
        "with_nvtx": [True, False],
    }
    default_options = {
        "header_only": False,  # also builds the jitify2_preprocess tool if False
        "v2": True,
        "with_nvtx": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if not self.options.v2:
            del self.options.with_nvtx
            del self.options.header_only
        if self.options.get_safe("header_only"):
            self.package_type = "header-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        if self.info.options.get_safe("header_only"):
            self.info.settings.clear()

    def requirements(self):
        self._utils.cuda_requires(self, "nvrtc", transitive_headers=True, transitive_libs=True)
        if self.options.v2:
            if Version(self.settings.cuda.version) >= "12.0":
                self._utils.cuda_requires(self, "nvjitlink", transitive_headers=True, transitive_libs=True)
            if self.options.with_nvtx:
                self._utils.cuda_requires(self, "nvtx", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_settings(self)
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if not self.options.get_safe("header_only"):
            tc = CMakeToolchain(self)
            tc.cache_variables["ENABLE_NVTX"] = self.options.with_nvtx
            tc.generate()
            deps = CMakeDeps(self)
            deps.generate()

    def build(self):
        if not self.options.get_safe("header_only"):
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if not self.options.get_safe("header_only"):
            cmake = CMake(self)
            cmake.install()
        copy(self, "jitify.hpp", self.source_folder, os.path.join(self.package_folder, "include"))
        if self.options.v2:
            for f in [
                "jitify2.hpp",
                "jitify2_preprocess.cpp",
                "stringify.cpp",
            ]:
                copy(self, f, self.source_folder, os.path.join(self.package_folder, "include"))

    def package_info(self):
        if self.options.get_safe("header_only"):
            self.cpp_info.libdirs = []
            self.cpp_info.bindirs = []
        if self.options.v2:
            self.cpp_info.srcdirs = ["include"]
            if self.options.with_nvtx:
                self.cpp_info.defines.append("JITIFY_ENABLE_NVTX=1")
