import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class LibdwarfConan(ConanFile):
    name = "libdwarf"
    description = "A library and a set of command-line tools for reading and writing DWARF2"
    license = "LGPL-2.1-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.prevanders.net/dwarf.html"
    topics = ("debug", "dwarf", "dwarf2", "elf")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_dwarfgen": [True, False],
        "with_dwarfdump": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_dwarfgen": False,
        "with_dwarfdump": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.license = ["LGPL-2.1-only"]
        if self.options.with_dwarfgen:
            self.license.append("BSD-2-Clause-Views")
        if self.options.with_dwarfdump:
            self.license.append("GPL-2.0-only")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")
        self.requires("zstd/[~1.5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["BUILD_NON_SHARED"] = not self.options.shared
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_DWARFGEN"] = self.options.with_dwarfgen
        tc.variables["BUILD_DWARFDUMP"] = self.options.with_dwarfdump
        tc.variables["BUILD_DWARFEXAMPLE"] = False
        if cross_building(self):
            tc.variables["HAVE_UNUSED_ATTRIBUTE_EXITCODE"] = "0"
            tc.variables["HAVE_UNUSED_ATTRIBUTE_EXITCODE__TRYRUN_OUTPUT"] = ""
        tc.generate()

        dpes = CMakeDeps(self)
        dpes.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "src", "lib", "libdwarf"))
        rename(self, os.path.join(self.package_folder, "licenses", "COPYING"), os.path.join(self.package_folder, "licenses", "COPYING-libdwarf"))
        if self.options.with_dwarfgen:
            copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "src", "bin", "dwarfgen"))
            rename(self, os.path.join(self.package_folder, "licenses", "COPYING"), os.path.join(self.package_folder, "licenses", "COPYING-dwarfgen"))
        if self.options.with_dwarfdump:
            copy(self, pattern="GPL.txt", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "src", "bin", "dwarfdump"))
            rename(self, os.path.join(self.package_folder, "licenses", "GPL.txt"), os.path.join(self.package_folder, "licenses", "COPYING-dwarfdump"))
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["dwarf"]
        if self.options.with_dwarfgen:
            self.cpp_info.libs.append("dwarfp")
        # It could be applied for all the versions and avoid those patches when #ifndef LIBDWARF_STATIC
        if Version(self.version) >= "2.1.0" and not self.options.shared:
            self.cpp_info.defines = ["LIBDWARF_STATIC=1"]
