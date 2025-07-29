import os

from conan import ConanFile
from conan.tools.build import stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class OpenEXRConan(ConanFile):
    name = "openexr"
    description = "OpenEXR is a high dynamic-range (HDR) image file format developed by Industrial Light & " \
                  "Magic for use in computer imaging applications."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/AcademySoftwareFoundation/openexr"
    topics = ("hdr", "image", "picture", "file format", "computer vision")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OPENEXR_BUILD_BOTH_STATIC_SHARED"] = False
        tc.variables["ILMBASE_BUILD_BOTH_STATIC_SHARED"] = False
        tc.variables["PYILMBASE_ENABLE"] = False
        tc.variables["INSTALL_OPENEXR_EXAMPLES"] = False
        tc.variables["INSTALL_OPENEXR_DOCS"] = False
        tc.variables["OPENEXR_BUILD_UTILS"] = False
        tc.variables["BUILD_TESTING"] = False
        tc.variables["CMAKE_SKIP_INSTALL_RPATH"] = True
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        # FIXME: we should generate 2 CMake config files: OpenEXRConfig.cmake and IlmBaseConfig.cmake
        #        waiting an implementation of https://github.com/conan-io/conan/issues/9000
        self.cpp_info.set_property("cmake_file_name", "OpenEXR")

        # Avoid conflict in PkgConfigDeps with OpenEXR.pc file coming from openexr_ilmimf component
        self.cpp_info.set_property("pkg_config_name", "openexr_conan_full_package")

        lib_suffix = ""
        if not self.options.shared or self.settings.os == "Windows":
            v = Version(self.version)
            lib_suffix += f"-{v.major}_{v.minor}"
        if self.settings.build_type == "Debug":
            lib_suffix += "_d"

        include_dir = os.path.join("include", "OpenEXR")

        # IlmImfConfig
        self.cpp_info.components["openexr_ilmimfconfig"].set_property("cmake_target_name", "OpenEXR::IlmImfConfig")
        self.cpp_info.components["openexr_ilmimfconfig"].includedirs.append(include_dir)

        # IlmImf
        self.cpp_info.components["openexr_ilmimf"].set_property("cmake_target_name", "OpenEXR::IlmImf")
        self.cpp_info.components["openexr_ilmimf"].set_property("pkg_config_name", "OpenEXR")
        self.cpp_info.components["openexr_ilmimf"].includedirs.append(include_dir)
        self.cpp_info.components["openexr_ilmimf"].libs = [f"IlmImf{lib_suffix}"]
        self.cpp_info.components["openexr_ilmimf"].requires = [
            "openexr_ilmimfconfig", "ilmbase_iex", "ilmbase_half",
            "ilmbase_imath", "ilmbase_ilmthread", "zlib-ng::zlib-ng",
        ]

        # IlmImfUtil
        self.cpp_info.components["openexr_ilmimfutil"].set_property("cmake_target_name", "OpenEXR::IlmImfUtil")
        self.cpp_info.components["openexr_ilmimfutil"].includedirs.append(include_dir)
        self.cpp_info.components["openexr_ilmimfutil"].libs = [f"IlmImfUtil{lib_suffix}"]
        self.cpp_info.components["openexr_ilmimfutil"].requires = ["openexr_ilmimfconfig", "openexr_ilmimf"]

        # IlmBaseConfig
        self.cpp_info.components["ilmbase_ilmbaseconfig"].set_property("cmake_target_name", "IlmBase::IlmBaseConfig")
        self.cpp_info.components["ilmbase_ilmbaseconfig"].includedirs.append(include_dir)

        # Half
        self.cpp_info.components["ilmbase_half"].set_property("cmake_target_name", "IlmBase::Half")
        self.cpp_info.components["ilmbase_half"].includedirs.append(include_dir)
        self.cpp_info.components["ilmbase_half"].libs = [f"Half{lib_suffix}"]
        self.cpp_info.components["ilmbase_half"].requires = ["ilmbase_ilmbaseconfig"]

        # Iex
        self.cpp_info.components["ilmbase_iex"].set_property("cmake_target_name", "IlmBase::Iex")
        self.cpp_info.components["ilmbase_iex"].includedirs.append(include_dir)
        self.cpp_info.components["ilmbase_iex"].libs = [f"Iex{lib_suffix}"]
        self.cpp_info.components["ilmbase_iex"].requires = ["ilmbase_ilmbaseconfig"]

        # IexMath
        self.cpp_info.components["ilmbase_iexmath"].set_property("cmake_target_name", "IlmBase::IexMath")
        self.cpp_info.components["ilmbase_iexmath"].includedirs.append(include_dir)
        self.cpp_info.components["ilmbase_iexmath"].libs = [f"IexMath{lib_suffix}"]
        self.cpp_info.components["ilmbase_iexmath"].requires = ["ilmbase_ilmbaseconfig", "ilmbase_iex"]

        # IMath
        self.cpp_info.components["ilmbase_imath"].set_property("cmake_target_name", "IlmBase::IMath")
        self.cpp_info.components["ilmbase_imath"].includedirs.append(include_dir)
        self.cpp_info.components["ilmbase_imath"].libs = [f"Imath{lib_suffix}"]
        self.cpp_info.components["ilmbase_imath"].requires = ["ilmbase_ilmbaseconfig", "ilmbase_half", "ilmbase_iexmath"]

        # IlmThread
        self.cpp_info.components["ilmbase_ilmthread"].set_property("cmake_target_name", "IlmBase::IlmThread")
        self.cpp_info.components["ilmbase_ilmthread"].includedirs.append(include_dir)
        self.cpp_info.components["ilmbase_ilmthread"].libs = [f"IlmThread{lib_suffix}"]
        self.cpp_info.components["ilmbase_ilmthread"].requires = ["ilmbase_ilmbaseconfig", "ilmbase_iex"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["ilmbase_ilmthread"].system_libs.append("pthread")

        # Convenient component to model official IlmBase.pc
        self.cpp_info.components["ilmbase_conan_pkgconfig"].set_property("pkg_config_name", "IlmBase")
        self.cpp_info.components["ilmbase_conan_pkgconfig"].requires = [
            "ilmbase_ilmbaseconfig", "ilmbase_half", "ilmbase_iex",
            "ilmbase_iexmath", "ilmbase_imath", "ilmbase_ilmthread"
        ]

        if self.options.shared and self.settings.os == "Windows":
            self.cpp_info.components["openexr_ilmimfconfig"].defines.append("OPENEXR_DLL")
            self.cpp_info.components["ilmbase_ilmbaseconfig"].defines.append("OPENEXR_DLL")

        if not self.options.shared:
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.components["openexr_ilmimfconfig"].system_libs.append(libcxx)
                self.cpp_info.components["ilmbase_ilmbaseconfig"].system_libs.append(libcxx)
