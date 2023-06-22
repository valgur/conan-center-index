# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
import os
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class Hdf4Conan(ConanFile):
    name = "hdf4"
    description = "HDF4 is a data model, library, and file format for storing and managing data."
    license = "BSD-3-Clause"
    topics = ("hdf", "data")
    homepage = "https://portal.hdfgroup.org/display/HDF4/HDF4"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "jpegturbo": [True, False],
        "szip_support": [None, "with_libaec", "with_szip"],
        "szip_encoding": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "jpegturbo": False,
        "szip_support": None,
        "szip_encoding": False,
    }

    exports_sources = ["CMakeLists.txt", "patches/**"]
    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if not bool(self.options.szip_support):
            del self.options.szip_encoding

    def requirements(self):
        self.requires("zlib/1.2.12")
        if self.options.jpegturbo:
            self.requires("libjpeg-turbo/2.1.2")
        else:
            self.requires("libjpeg/9d")
        if self.options.szip_support == "with_libaec":
            self.requires("libaec/1.0.6")
        elif self.options.szip_support == "with_szip":
            self.requires("szip/2.1.1")

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], destination=self._source_subfolder, strip_root=True
        )

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["HDF4_EXTERNALLY_CONFIGURED"] = True
        tc.variables["HDF4_EXTERNAL_LIB_PREFIX"] = ""
        tc.variables["HDF4_NO_PACKAGES"] = True
        tc.variables["ONLY_SHARED_LIBS"] = self.options.shared
        tc.variables["HDF4_ENABLE_COVERAGE"] = False
        tc.variables["HDF4_ENABLE_DEPRECATED_SYMBOLS"] = True
        tc.variables[
            "HDF4_ENABLE_JPEG_LIB_SUPPORT"
        ] = True  # HDF can't compile without libjpeg or libjpeg-turbo
        tc.variables["HDF4_ENABLE_Z_LIB_SUPPORT"] = True  # HDF can't compile without zlib
        tc.variables["HDF4_ENABLE_SZIP_SUPPORT"] = bool(self.options.szip_support)
        tc.variables["HDF4_ENABLE_SZIP_ENCODING"] = self.options.get_safe("szip_encoding") or False
        tc.variables["HDF4_PACKAGE_EXTLIBS"] = False
        tc.variables["HDF4_BUILD_XDR_LIB"] = True
        tc.variables["BUILD_TESTING"] = False
        tc.variables["HDF4_INSTALL_INCLUDE_DIR"] = os.path.join(
            self.package_folder, "include", "hdf4"
        )
        tc.variables["HDF4_BUILD_FORTRAN"] = False
        tc.variables["HDF4_BUILD_UTILS"] = False
        tc.variables["HDF4_BUILD_TOOLS"] = False
        tc.variables["HDF4_BUILD_EXAMPLES"] = False
        tc.variables["HDF4_BUILD_JAVA"] = False
        if tools.cross_building(self):
            tc.variables["H4_PRINTF_LL_TEST_RUN"] = "0"
            tc.variables["H4_PRINTF_LL_TEST_RUN__TRYRUN_OUTPUT"] = ""
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        os.remove(os.path.join(self.package_folder, "lib", "libhdf4.settings"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "hdf"
        unofficial_includedir = os.path.join(self.package_folder, "include", "hdf4")
        # xdr
        xdr_cmake = "xdr-shared" if self.options.shared else "xdr-static"
        self.cpp_info.components["xdr"].names["cmake_find_package"] = xdr_cmake
        self.cpp_info.components["xdr"].names["cmake_find_package_multi"] = xdr_cmake
        self.cpp_info.components["xdr"].includedirs.append(unofficial_includedir)
        self.cpp_info.components["xdr"].libs = [self._get_decorated_lib("xdr")]
        if self.settings.os == "Windows":
            self.cpp_info.components["xdr"].system_libs.append("ws2_32")
        # hdf
        hdf_cmake = "hdf-shared" if self.options.shared else "hdf-static"
        self.cpp_info.components["hdf"].names["cmake_find_package"] = hdf_cmake
        self.cpp_info.components["hdf"].names["cmake_find_package_multi"] = hdf_cmake
        self.cpp_info.components["hdf"].includedirs.append(unofficial_includedir)
        self.cpp_info.components["hdf"].libs = [self._get_decorated_lib("hdf")]
        self.cpp_info.components["hdf"].requires = [
            "zlib::zlib",
            "libjpeg-turbo::libjpeg-turbo" if self.options.jpegturbo else "libjpeg::libjpeg",
        ]
        if self.options.szip_support == "with_libaec":
            self.cpp_info.components["hdf"].requires.append("libaec::libaec")
        elif self.options.szip_support == "with_szip":
            self.cpp_info.components["hdf"].requires.append("szip::szip")
        # mfhdf
        mfhdf_cmake = "mfhdf-shared" if self.options.shared else "mfhdf-static"
        self.cpp_info.components["mfhdf"].names["cmake_find_package"] = mfhdf_cmake
        self.cpp_info.components["mfhdf"].names["cmake_find_package_multi"] = mfhdf_cmake
        self.cpp_info.components["mfhdf"].includedirs.append(unofficial_includedir)
        self.cpp_info.components["mfhdf"].libs = [self._get_decorated_lib("mfhdf")]
        self.cpp_info.components["mfhdf"].requires = ["xdr", "hdf"]

        if self.options.shared:
            self.cpp_info.components["xdr"].defines.append("H4_BUILT_AS_DYNAMIC_LIB=1")
            self.cpp_info.components["hdf"].defines.append("H4_BUILT_AS_DYNAMIC_LIB=1")
            self.cpp_info.components["mfhdf"].defines.append("H4_BUILT_AS_DYNAMIC_LIB=1")

    def _get_decorated_lib(self, name):
        libname = name
        if self.settings.os == "Windows" and self.settings.compiler != "gcc" and not self.options.shared:
            libname = "lib" + libname
        if self.settings.build_type == "Debug":
            libname += "_D" if self.settings.os == "Windows" else "_debug"
        return libname
