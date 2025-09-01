import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GlomapConan(ConanFile):
    name = "glomap"
    description = "GLOMAP is a general purpose global structure-from-motion pipeline for image-based reconstruction"
    license = "BSD-3-Clause"
    homepage = "https://github.com/colmap/glomap"
    topics = ("sfm", "structure-from-motion", "3d-reconstruction", "computer-vision", "colmap")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cuda": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)

    def package_id(self):
        if self.info.options.cuda:
            # No device code is built for CUDA
            del self.info.settings.cuda.architectures

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.cuda:
            del self.settings.cuda
        else:
            self.options["colmap"].cuda = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("colmap/[^3.12]", transitive_headers=True, transitive_libs=True)
        self.requires("poselib/[^2.0.5]", transitive_headers=True, transitive_libs=True)
        self.requires("suitesparse-cholmod/[^5.3.0]")
        self.requires("openmp/system")
        if self.options.cuda:
            self._utils.cuda_requires(self, "cudart")
            self._utils.cuda_requires(self, "curand")

    def validate(self):
        check_min_cppstd(self, 17)
        if not self.dependencies["ceres-solver"].options.use_suitesparse:
            raise ConanInvalidConfiguration("'-o ceres-solver/*:use_suitesparse=True' is required")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.28]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Don't enable CUDA as a language in CMake:
        # requires nvcc despite no device code being built
        replace_in_file(self, "cmake/FindDependencies.cmake", "enable_language(CUDA)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CUDA_ENABLED"] = self.options.cuda
        tc.cache_variables["FETCH_COLMAP"] = False
        tc.cache_variables["FETCH_POSELIB"] = False
        tc.cache_variables["TESTS_ENABLED"] = False
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

    def package_info(self):
        self.cpp_info.libs = ["glomap"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
