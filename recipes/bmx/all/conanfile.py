import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class BmxConan(ConanFile):
    name = "bmx"
    description = (
        "Library for handling broadcast/production oriented media file formats. "
        "Allows reading, modifying and writing media metadata and file essences."
    )
    topics = ("vfx", "image", "picture", "video", "multimedia", "mxf")
    license = "BSD-3-Clause"
    homepage = "https://github.com/bbc/bmx"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libcurl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libcurl": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        # Required libraries
        self.requires("uriparser/[>=0.9.8 <1]")
        self.requires("expat/[>=2.6.2 <3]")

        if not (self.settings.os == 'Windows' or self.settings.os == 'Macos'):
            self.requires('libuuid/1.0.3')

        # Configuration dependent requirements
        if self.options.with_libcurl:
            self.requires("libcurl/[>=7.78.0 <9]")

    def validate(self):
        # Supported platforms based on
        # https://github.com/bbc/bmx/blob/v1.3/deps/libMXF/tools/MXFDump/MXFDump.cpp#L48-L327
        if self.settings.arch == "armv8" and self.settings.os != "Macos":
            raise ConanInvalidConfiguration(f"Unsupported platform: {self.settings.arch} {self.settings.os}")
        elif self.settings.arch not in ["x86", "x86_64"] and not self.settings.arch.startswith("ppc") and not self.settings.arch.startswith("sparc"):
            raise ConanInvalidConfiguration(f"Unsupported arch: {self.settings.arch}")

        check_min_cppstd(self, 11)

        # Symbol export is currently not working properly on Windows so shared
        # libraries are currently deactivated. This can later be revisited based
        # on https://github.com/bbc/bmx/issues/80
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration(
                "Building as a shared library currently not supported on Windows!"
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BMX_BUILD_WITH_LIBCURL"] = self.options.with_libcurl
        tc.generate()

        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    @staticmethod
    def _conan_comp(name):
        return f"bmx_{name.lower()}"

    def _add_component(self, name):
        component = self.cpp_info.components[self._conan_comp(name)]
        component.set_property("cmake_target_name", f"bmx::{name}")
        return component

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "bmx")
        self.cpp_info.set_property("pkg_config_name", "bmx")

        # bbc-bmx::MXF
        libmxf = self._add_component("MXF")
        libmxf.libs = ["MXF"]
        libmxf.requires = []
        if not (self.settings.os == 'Windows' or self.settings.os == 'Macos'):
            libmxf.requires.append("libuuid::libuuid")

        # bbc-bmx::MXF++
        libmxfpp = self._add_component("MXF++")
        libmxfpp.libs = ["MXF++"]
        libmxfpp.requires = [
            "bmx_mxf"
        ]

        # bbc-bmx::bmx
        libbmx = self._add_component("bmx")
        libbmx.libs = ["bmx"]
        libbmx.requires = [
            "bmx_mxf",
            "bmx_mxf++",
            "expat::expat",
            "uriparser::uriparser",
        ]
        if not (self.settings.os == 'Windows' or self.settings.os == 'Macos'):
            libbmx.requires.append("libuuid::libuuid")

        if self.options.with_libcurl:
            libbmx.requires.append("libcurl::libcurl")
