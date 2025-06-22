import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, check_min_cstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ArmComputeLibraryConan(ConanFile):
    name = "arm-compute-library"
    description = ("The Compute Library is a collection of low-level machine learning functions "
                   "optimized for Arm Cortex-A, Arm Neoverse and Arm Mali GPUs architectures.")
    license = "MIT AND Apache-2.0 AND BSD-3-Clause"
    homepage = "https://github.com/ARM-software/ComputeLibrary"
    topics = ("arm", "machine-learning", "computer-vision", "neon", "opencl")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "threads": ["openmp", "cppthreads", "none"],
        "logging": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "threads": "openmp",
        "logging": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("kleidiai/[>=0.5.0 <2]")
        self.requires("opencl-headers/[*]", transitive_headers=True)
        self.requires("half/[>=1.12.0 <3]", transitive_headers=True)
        self.requires("libnpy/[^1.0.1]", transitive_headers=True)
        self.requires("stb/[*]", transitive_headers=True)
        if self.options.threads == "openmp":
            self.requires("openmp/system")

    def validate(self):
        if not str(self.settings.arch).startswith("arm"):
            raise ConanInvalidConfiguration("This recipe only supports Arm architectures.")
        check_min_cppstd(self, 14)
        if self.settings.compiler.get_safe("cstd"):
            check_min_cstd(self, 99)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Unvendor third-party dependencies
        rmdir(self, "include/CL")
        rmdir(self, "include/half")
        rmdir(self, "include/libnpy")
        rmdir(self, "include/stb")
        rmdir(self, "third_party")
        replace_in_file(self, "arm_compute/AclOpenClExt.h", "include/CL/cl.h", "CL/cl.h")
        replace_in_file(self, "support/Half.h", "half/half.hpp", "half.hpp")
        replace_in_file(self, "utils/Utils.h", "libnpy/npy.hpp", "npy.hpp")
        replace_in_file(self, "utils/ImageLoader.h", "stb/stb_image.h", "stb_image.h")
        replace_in_file(self, "utils/Utils.cpp", "stb/stb_image.h", "stb_image.h")
        replace_in_file(self, "src/CMakeLists.txt", "../third_party/kleidiai", "# ../third_party/kleidiai")
        # Append instead of setting for conan_deps.cmake
        replace_in_file(self, "cmake/compilers/setup.cmake",
                        "ARM_COMPUTE_LINK_LIBS",
                        "ARM_COMPUTE_LINK_LIBS ${ARM_COMPUTE_LINK_LIBS}")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_ArmCompute_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["ARM_COMPUTE_BUILD_SHARED_LIB"] = self.options.shared
        tc.cache_variables["ARM_COMPUTE_ENABLE_OPENMP"] = self.options.threads == "openmp"
        tc.cache_variables["ARM_COMPUTE_ENABLE_CPPTHREADS"] = self.options.threads == "cppthreads"
        tc.cache_variables["ARM_COMPUTE_ENABLE_LOGGING"] = self.options.logging
        # Consider overriding these CMake variables controlling -march flags in your profile
        #   ARM_COMPUTE_ARCH=armv8-a
        #   ARM_COMPUTE_CORE_FP16_ARCH=armv8.2-a+fp16
        #   ARM_COMPUTE_SVE_ARCH=armv8.2-a+sve+fp16+dotprod
        #   ARM_COMPUTE_SVE2_ARCH=armv8.6-a+sve2+fp16+dotprod
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # The CMake project is somewhat incomplete compared to the SCons and Bazel ones - no headers are installed
        copy(self, "*", os.path.join(self.source_folder, "arm_compute"), os.path.join(self.package_folder, "include", "arm_compute", "arm_compute"))
        copy(self, "*.h", os.path.join(self.source_folder, "support"), os.path.join(self.package_folder, "include", "arm_compute", "support"))
        copy(self, "*.h", os.path.join(self.source_folder, "utils"), os.path.join(self.package_folder, "include", "arm_compute", "utils"))
        copy(self, "*", os.path.join(self.source_folder, "scripts"), os.path.join(self.package_folder, "share", "arm_compute", "scripts"))
        # Also include internal headers for OpenVINO
        copy(self, "*.h", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "include", "arm_compute", "src"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        # Not CMake config or .pc files are installed
        self.cpp_info.libs = ["arm_compute", "arm_compute_graph"]
        self.cpp_info.includedirs = ["include", os.path.join("include", "arm_compute")]
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread", "dl"]
