import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibLASConan(ConanFile):
    name = "liblas"
    description = "C++ library and programs for reading and writing ASPRS LAS format with LiDAR data"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://liblas.org/"
    topics = ("point-cloud", "lidar", "las")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_gdal": [True, False],
        "with_geotiff": [True, False],
        "with_laszip": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_gdal": False,
        "with_geotiff": True,
        "with_laszip": True,
        "tools": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # boost/[^1.42]
        self.requires("boost/1.86.0", transitive_headers=True, transitive_libs=True)
        if self.options.with_gdal:
            self.requires("gdal/[^3]")
        if self.options.with_geotiff:
            self.requires("libgeotiff/[^1.7.1]")
            self.requires("proj/[^9.3.1]")
        if self.options.with_laszip:
            self.requires("laszip/[^2.0.2]")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.11)",
                        "cmake_minimum_required(VERSION 3.14)")

        # Respect cppstd from Conan
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD", "# set(CMAKE_CXX_STANDARD")

        # Fix broken attempt at adding dependencies to RPATH
        replace_in_file(self, "apps/CMakeLists.txt", "get_filename_component(", "# get_filename_component(")

        # Allow newer major versions of dependencies
        replace_in_file(self, "CMakeLists.txt", "GDAL 1.7.0", "GDAL REQUIRED")
        replace_in_file(self, "CMakeLists.txt", "GeoTIFF 1.3.0", "GeoTIFF REQUIRED")
        replace_in_file(self, "CMakeLists.txt", "LASzip 2.0.1", "LASzip REQUIRED")

        # Add support for GDAL 2.5 and newer
        replace_in_file(self, "src/gt_wkt_srs.cpp",
                        "oSRS.FixupOrdering();",
                        "oSRS.SetAxisMappingStrategy(OAMS_TRADITIONAL_GIS_ORDER);")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["WITH_UTILITIES"] = self.options.tools
        tc.cache_variables["WITH_TESTS"] = False
        tc.cache_variables["BUILD_OSGEO4W"] = False
        tc.cache_variables["WITH_GDAL"] = self.options.with_gdal
        tc.cache_variables["WITH_GEOTIFF"] = self.options.with_geotiff
        tc.cache_variables["GEOTIFF_FOUND"] = self.options.with_geotiff
        tc.cache_variables["GEOTIFF_LIBRARY"] = "geotiff_library"
        tc.cache_variables["WITH_LASZIP"] = self.options.with_laszip
        if self.options.with_laszip:
            tc.cache_variables["LASZIP_FOUND"] = True
            tc.cache_variables["WITH_STATIC_LASZIP"] = not self.dependencies["laszip"].options.shared
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("laszip", "cmake_file_name", "LASzip")
        deps.set_property("laszip", "cmake_additional_variables_prefixes", ["LASZIP"])
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
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libLAS")

        self.cpp_info.components["las"].set_property("cmake_target_name", "las")
        self.cpp_info.components["las"].libs = ["las"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["las"].system_libs.extend(["m", "pthread"])
        self.cpp_info.components["las"].requires = [
            "boost::iostreams",
            "boost::program_options",
            "boost::serialization",
            "boost::thread",
        ]
        if self.options.with_gdal:
            self.cpp_info.components["las"].requires.append("gdal::gdal")
        if self.options.with_geotiff:
            self.cpp_info.components["las"].requires.extend(["libgeotiff::libgeotiff", "proj::proj"])
        if self.options.with_laszip:
            self.cpp_info.components["las"].requires.append("laszip::laszip")

        self.cpp_info.components["las_c"].set_property("cmake_target_name", "las_c")
        self.cpp_info.components["las_c"].set_property("pkg_config_name", "liblas")
        self.cpp_info.components["las_c"].libs = ["las_c"]
        self.cpp_info.components["las_c"].requires = ["las"]
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.components["las_c"].system_libs.append(stdcpp_library(self))
