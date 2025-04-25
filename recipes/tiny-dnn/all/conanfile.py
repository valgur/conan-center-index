import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class TinyDnnConan(ConanFile):
    name = "tiny-dnn"
    description = "tiny-dnn is a C++14 implementation of deep learning."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/tiny-dnn/tiny-dnn"
    topics = ("header-only", "deep-learning", "embedded", "iot", "computational")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {"with_tbb": [True, False]}
    default_options = {"with_tbb": False}

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cereal/1.3.1")
        self.requires("stb/cci.20250314")
        if self.options.with_tbb:
            self.requires("onetbb/2020.3")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_TBB"] = self.options.with_tbb
        tc.variables["USE_GEMMLOWP"] = False
        # Ensure auto-detection of dependencies is disabled
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_TBB"] = not self.options.with_tbb
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_NNPACK"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_OpenCL"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_GreenteaLibDNN"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        replace_in_file(self,
                        os.path.join(self.source_folder, "tiny_dnn", "util", "image.h"),
                        "third_party/", "")

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.configure()
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("cmake_file_name", "tinydnn")
        self.cpp_info.set_property("cmake_target_name", "TinyDNN::tiny_dnn")

        self.cpp_info.requires = ["cereal::cereal", "stb::stb"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        if self.options.with_tbb:
            self.cpp_info.defines = ["CNN_USE_TBB=1"]
            self.cpp_info.requires.append("onetbb::onetbb")
