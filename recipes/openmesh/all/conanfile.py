from conan import ConanFile
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.microsoft import is_msvc
import os

required_conan_version = ">=2.1"


class OpenmeshConan(ConanFile):
    name = "openmesh"
    description = "OpenMesh is a generic and efficient data structure for " \
                  "representing and manipulating polygonal meshes."
    license = "BSD-3-Clause"
    topics = ("mesh", "structure", "geometry")
    homepage = "https://www.graphics.rwth-aachen.de/software/openmesh"
    url = "https://github.com/conan-io/conan-center-index"

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

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.settings.os == "Windows":
            tc.variables["OPENMESH_BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_APPS"] = False
        tc.variables["OPENMESH_DOCS"] = False
        if not valid_min_cppstd(self, self._min_cppstd):
            tc.variables["CMAKE_CXX_STANDARD"] = self._min_cppstd
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "libdata"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.settings.os != "Windows":
            rm(self, "*.a" if self.options.shared else "*.[so|dylib]*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenMesh")
        self.cpp_info.set_property("pkg_config_name", "openmesh")

        suffix = "d" if self.settings.build_type == "Debug" else ""
        # OpenMeshCore
        self.cpp_info.components["openmeshcore"].set_property("cmake_target_name", "OpenMeshCore")
        self.cpp_info.components["openmeshcore"].libs = ["OpenMeshCore" + suffix]
        if not self.options.shared:
            self.cpp_info.components["openmeshcore"].defines.append("OM_STATIC_BUILD")
        if is_msvc(self):
            self.cpp_info.components["openmeshcore"].defines.append("_USE_MATH_DEFINES")

        # OpenMeshTools
        self.cpp_info.components["openmeshtools"].set_property("cmake_target_name", "OpenMeshTools")
        self.cpp_info.components["openmeshtools"].libs = ["OpenMeshTools" + suffix]
        self.cpp_info.components["openmeshtools"].requires = ["openmeshcore"]
