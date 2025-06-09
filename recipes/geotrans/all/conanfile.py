import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GeotransConan(ConanFile):
    name = "geotrans"
    description = "MSP GEOTRANS is the NGA and DOD approved coordinate converter and datum translator."
    license = "NGA GEOTRANS ToS (https://earth-info.nga.mil/php/download.php?file=wgs-terms)"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://earth-info.nga.mil/"
    topics = ("geotrans", "geodesic", "geographic", "coordinate", "datum", "geodetic", "conversion", "transformation")
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
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.txt",
                   src=os.path.join(self.source_folder, "GEOTRANS3", "docs"),
                   dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["dtcc"].libs = ["MSPdtcc"]
        self.cpp_info.components["dtcc"].resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["dtcc"].system_libs.append("pthread")
            self.cpp_info.components["dtcc"].system_libs.append("m")

        self.cpp_info.components["ccs"].libs = ["MSPCoordinateConversionService"]
        self.cpp_info.components["ccs"].requires = ["dtcc"]
        self.cpp_info.components["ccs"].resdirs = ["share"]

        mspccs_data_path = os.path.join(self.package_folder, "share")
        self.runenv_info.define_path("MSPCCS_DATA", mspccs_data_path)
