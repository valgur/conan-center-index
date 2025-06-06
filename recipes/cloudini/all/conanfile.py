import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CloudiniConan(ConanFile):
    name = "cloudini"
    description = ("Cloudini is a pointcloud compression library. "
                   "Its main focus is speed, but it still achieves very good compression ratios.")
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/facontidavide/cloudini"
    topics = ("point-clouds", "compression")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_draco": [True, False],
        "with_pcl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_draco": False,
        "with_pcl": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src", "cloudini_lib"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("lz4/[^1.9.4]")
        self.requires("zstd/[~1.5]")
        if self.options.with_draco:
            self.requires("draco/[^1.5]")
        if self.options.with_pcl:
            self.requires("pcl/[^1.14]")
        if self.options.tools:
            self.requires("mcap/[>=1.4 <3]")
            self.requires("cxxopts/[^3.0]")

    def validate(self):
        check_min_cppstd(self, 20)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        cmakelists = os.path.join(self.source_folder, "cloudini_lib", "CMakeLists.txt")
        # Use actual CMake targets
        replace_in_file(self, cmakelists, "${LZ4_LIBRARY}", "lz4::lz4")
        replace_in_file(self, cmakelists, "${ZSTD_LIBRARY}", "zstd::libzstd")
        replace_in_file(self, cmakelists, "${DRACO_LIBRARY}", "$<TARGET_NAME_IF_EXISTS:draco::draco>")
        replace_in_file(self, cmakelists, "${PCL_LIBRARIES}", "$<TARGET_NAME_IF_EXISTS:PCL::common>")
        # Disable CPM
        save(self, "cloudini_lib/cmake/CPM.cmake", "")
        # unvendor cxxopts
        replace_in_file(self, "cloudini_lib/tools/CMakeLists.txt", 'CPMAddPackage("gh:jarro2783/cxxopts@3.3.1")', "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_cloudini_lib_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["CLOUDINI_BUILD_TOOLS"] = self.options.tools
        tc.cache_variables["CLOUDINI_BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["WITH_DRACO"] = self.options.with_draco
        tc.cache_variables["WITH_PCL"] = self.options.with_pcl
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_ament_cmake"] = True
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_draco"] = not self.options.with_draco
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_PCL"] = not self.options.with_pcl
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("cxxopts", "cmake_target_name", "cxxopts")
        deps.set_property("mcap", "cmake_target_name", "mcap")
        deps.set_property("zstd", "cmake_target_name", "zstd::libzstd")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cloudini_lib")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        # No official CMake config or pkg-config files are exported
        self.cpp_info.libs = ["cloudini_lib"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
