import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class VilibConan(ConanFile):
    name = "vilib"
    description = "CUDA Visual Library by RPG. GPU-Accelerated Frontend for High-Speed VIO."
    license = "BSD-3-Clause"
    homepage = "https://github.com/uzh-rpg/vilib"
    topics = ("computer-vision", "visual-odometry", "visual-features", "cuda")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("opencv/[^4.5]", transitive_headers=True, transitive_libs=True, options={"highgui": True})
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("Shared builds on Windows are not supported")
        self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "assets")
        rmdir(self, "ros")
        rmdir(self, os.path.join("visual_lib", "test"))
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", " -Werror", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "vilib")
        self.cpp_info.set_property("cmake_target_name", "vilib::vilib")
        self.cpp_info.libs = ["vilib"]
        self.cpp_info.requires = [
            "eigen::eigen",
            "opencv::opencv_core",
            "opencv::opencv_imgproc",
            "opencv::opencv_features2d",
            "opencv::opencv_highgui",
            "cudart::cudart_",
        ]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "dl", "m", "rt"]
