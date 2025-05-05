import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class NetcdfConan(ConanFile):
    name = "netcdf"
    description = (
        "The Unidata network Common Data Form (netCDF) is an interface for "
        "scientific data access and a freely-distributed software library "
        "that provides an implementation of the interface."
    )
    topics = "unidata", "unidata-netcdf", "networking"
    license = "BSD-3-Clause"
    homepage = "https://github.com/Unidata/netcdf-c"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "netcdf4": [True, False],
        "cdf5": [True, False],
        "dap": [True, False],
        "byterange": [True, False],
        "logging": [True, False],
        "with_hdf5": [True, False],
        "with_szip": [True, False],
        "with_bz2": [True, False],
        "with_blosc": [True, False],
        "with_zstd": [True, False],
        "with_zip": [True, False],
        "with_libxml2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "netcdf4": True,
        "cdf5": True,
        "dap": True,
        "byterange": False,
        "logging": False,
        "with_hdf5": True,
        "with_szip": False,
        "with_bz2": True,
        "with_blosc": True,
        "with_zstd": True,
        "with_zip": True,
        "with_libxml2": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    @property
    def _with_hdf5(self):
        return self.options.with_hdf5 or self.options.netcdf4

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")
        if self.options.dap or self.options.byterange:
            self.requires("libcurl/[>=7.78.0 <9]")
        if self._with_hdf5:
            self.requires("hdf5/[^1.8.15]")
        if self.options.with_szip:
            self.requires("szip/[^2.1]")
        if self.options.with_bz2:
            self.requires("bzip2/[^1.0.8]")
        if self.options.with_blosc:
            self.requires("c-blosc/[^1.21.0]")
        if self.options.with_zstd:
            self.requires("zstd/[~1.5]")
        if self.options.with_zip:
            self.requires("libzip/[^1.7.3]")
        if self.options.with_libxml2:
            self.requires("libxml2/[^2.12.5]")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20.0 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # This breaks CMakeDeps targets otherwise
        replace_in_file(self, os.path.join("plugins", "CMakeLists.txt"), 'set(CMAKE_BUILD_TYPE "")', "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["NETCDF_BUILD_UTILITIES"] = False
        tc.cache_variables["NETCDF_ENABLE_TESTS"] = False
        tc.cache_variables["NETCDF_ENABLE_FILTER_TESTING"] = False

        tc.cache_variables["NETCDF_ENABLE_LOGGING"] = self.options.logging
        tc.cache_variables["NETCDF_ENABLE_CDF5"] = self.options.cdf5
        tc.cache_variables["NETCDF_ENABLE_DAP"] = self.options.dap
        tc.cache_variables["NETCDF_ENABLE_BYTERANGE"] = self.options.byterange
        tc.cache_variables["NETCDF_ENABLE_HDF5"] = self.options.with_hdf5
        tc.cache_variables["NETCDF_ENABLE_FILTER_SZIP"] = self.options.with_szip
        tc.cache_variables["NETCDF_ENABLE_FILTER_BZ2"] = self.options.with_bz2
        tc.cache_variables["NETCDF_ENABLE_FILTER_BLOSC"] = self.options.with_blosc
        tc.cache_variables["NETCDF_ENABLE_FILTER_ZSTD"] = self.options.with_zstd
        tc.cache_variables["NETCDF_ENABLE_NCZARR_ZIP"] = self.options.with_zip
        tc.cache_variables["NETCDF_ENABLE_LIBXML2"] = self.options.with_libxml2
        tc.cache_variables["NETCDF_ENABLE_S3"] = False
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("c-blosc", "cmake_file_name", "Blosc")
        deps.set_property("bzip2", "cmake_file_name", "Bz2")
        deps.set_property("szip", "cmake_file_name", "Szip")
        deps.set_property("libzip", "cmake_file_name", "Zip")
        deps.set_property("zlib", "cmake_file_name", "ZLIB")
        deps.set_property("zstd", "cmake_file_name", "Zstd")
        deps.set_property("hdf5", "cmake_file_name", "HDF5")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYRIGHT", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rm(self, "nc-config", os.path.join(self.package_folder, "bin"))
        rm(self, "*.settings", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.settings.os == "Windows" and self.options.shared:
            for vc_file in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
                rm(self, vc_file, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "netCDF")
        self.cpp_info.set_property("cmake_target_name", "netCDF::netcdf")
        self.cpp_info.set_property("pkg_config_name", "netcdf")
        self.cpp_info.libs = ["netcdf"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "m"]
        elif self.settings.os == "Windows":
            if self.options.shared:
                self.cpp_info.defines.append("DLL_NETCDF")
