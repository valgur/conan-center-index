from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.scm import Version
import os

required_conan_version = ">=1.53.0"


class CsmConan(ConanFile):
    name = "csm"
    description = "Community Sensor Model base interface library"
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ngageoint/csm"
    topics = ("sensor", "camera", "camera-model", "geospatial", "planetary", "planetary-data")

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

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CSM_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["CSM_VERSION"] = self.version
        tc.variables["CSM_MAJOR_VERSION"] = str(Version(self.version).major)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["csmapi"]
