import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CatalystConan(ConanFile):
    name = "catalyst"
    license = "BSD-3-Clause"
    description = "Catalyst is an API specification developed for simulations (and other scientific data producers) to analyze and visualize data in situ."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.kitware.com/paraview/catalyst"
    topics = ("simulation", "visualization", "paraview", "in-situ", "in-transit")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_mpi": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_mpi": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_mpi:
            self.requires("openmpi/[^5.0]")
        # TODO: unvendor conduit

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CATALYST_BUILD_REPLAY"] = False
        tc.variables["CATALYST_BUILD_TESTING"] = False
        tc.variables["CATALYST_BUILD_TOOLS"] = self.options.tools
        tc.variables["CATALYST_BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["CATALYST_USE_MPI"] = self.options.with_mpi
        # Catalyst adds by default catalyst_${VERSION} as suffix for static libs. Remove that
        if not self.options.shared:
            tc.variables["CATALYST_CUSTOM_LIBRARY_SUFFIX"] = ""
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _cmake_dir(self):
        return os.path.join("lib", "cmake", "catalyst-2.0")

    def package(self):
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rm(self, "catalyst-config*.cmake", os.path.join(self.package_folder, self._cmake_dir))
        rm(self, "catalyst-targets*.cmake", os.path.join(self.package_folder, self._cmake_dir))

    @property
    def _lib_suffix(self):
        return "d" if self.settings.os == "Windows" and self.settings.build_type == "Debug" else ""

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "catalyst")

        self.cpp_info.components["catalyst_headers"].set_property("cmake_target_name", "catalyst::catalyst_headers")
        self.cpp_info.components["catalyst_headers"].includedirs = ["include/catalyst-2.0"]
        self.cpp_info.components["catalyst_headers"].builddirs.append(self._cmake_dir)
        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_dir, "catalyst-macros.cmake")])

        self.cpp_info.components["catalyst_"].set_property("cmake_target_name", "catalyst::catalyst")
        self.cpp_info.components["catalyst_"].includedirs = ["include/catalyst-2.0"]
        self.cpp_info.components["catalyst_"].libs = ["catalyst" + self._lib_suffix]
        self.cpp_info.components["catalyst_"].requires = ["catalyst_headers"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["catalyst_"].system_libs.extend(["dl", "m"])
        if self.options.with_mpi:
            self.cpp_info.components["catalyst_"].requires.append("openmpi::ompi-c")

        self.cpp_info.components["catalyst_stub"].set_property("cmake_target_name", "catalyst::catalyst_stub")
        if self.options.shared:
            self.cpp_info.components["catalyst_stub"].libdirs = [os.path.join("lib", "catalyst")]
        self.cpp_info.components["catalyst_stub"].libs = ["catalyst-stub" + self._lib_suffix]
        self.cpp_info.components["catalyst_stub"].requires = ["catalyst_"]
