import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LibE57FormatConan(ConanFile):
    name = "libe57format"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/asmaloney/libE57Format"
    description = "Library for reading & writing the E57 file format"
    topics = ("e57", "io", "point-cloud")

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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("xerces-c/[^3.2.5]")

    def validate(self):
        check_min_cppstd(self, "11")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16.3 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        venv = VirtualBuildEnv(self)
        venv.generate()
        tc = CMakeToolchain(self)
        tc.variables["E57_BUILD_SHARED"] = self.options.shared
        tc.variables["E57_BUILD_TEST"] = False
        tc.variables["USING_STATIC_XERCES"] = not self.dependencies["xerces-c"].options.shared
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "POSITION_INDEPENDENT_CODE ON", "")
        if Version(self.version) >= "3.0":
            # Disable compiler warnings, which cause older versions of GCC to fail due to unrecognized flags
            replace_in_file(self, os.path.join(self.source_folder, "cmake", "CompilerWarnings.cmake"),
                            " -W", " # -W")
            # Disable warnings as errors
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "set_warning_as_error()", "", strict=False)

    def build(self):
        self._patch_sources()
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "e57format")
        self.cpp_info.set_property("cmake_target_name", "E57Format")
        suffix = "-d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"E57Format{suffix}"]
        if self.settings.os in ["Linux", "FreeBSD"] and not self.options.shared:
            self.cpp_info.system_libs.extend(["m", "pthread"])
