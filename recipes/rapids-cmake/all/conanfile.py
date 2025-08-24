import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class RapidsCMakeConan(ConanFile):
    name = "rapids-cmake"
    description = "A collection of CMake modules that are useful for all CUDA RAPIDS projects"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/rapids-cmake"
    topics = ("nvidia", "rapids", "cmake")
    package_type = "build-scripts"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Set the root dir variable otherwise set by RAPIDS.cmake
        replace_in_file(self, "rapids-cmake/rapids-cmake.cmake",
                        "include_guard(GLOBAL)",
                        "include_guard(GLOBAL)\n"
                        'set(rapids-cmake-dir "${CMAKE_CURRENT_LIST_DIR}")')
        # Fix version parsing
        replace_in_file(self, "rapids-cmake/rapids-version.cmake", "/../VERSION", "/VERSION")
        replace_in_file(self, "rapids-cmake/rapids-version.cmake", "/../RAPIDS_BRANCH", "/RAPIDS_BRANCH")
        # Don't force an exact CCCL version
        replace_in_file(self, "rapids-cmake/cpm/cccl.cmake", "FIND_PACKAGE_ARGUMENTS EXACT", "")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*",
             os.path.join(self.source_folder, "rapids-cmake"),
             os.path.join(self.package_folder, "share/rapids-cmake"))
        copy(self, "VERSION", self.source_folder, os.path.join(self.package_folder, "share/rapids-cmake"))
        copy(self, "RAPIDS_BRANCH", self.source_folder, os.path.join(self.package_folder, "share/rapids-cmake"))

    def package_info(self):
        self.cpp_info.builddirs = ["share/rapids-cmake"]
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_build_modules", ["share/rapids-cmake/rapids-cmake.cmake"])
