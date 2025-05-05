import glob
import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class FoxiConan(ConanFile):
    name = "foxi"
    description = "ONNXIFI with Facebook Extension."
    license = "MIT"
    topics = ("foxi", "onnxifi")
    homepage = "https://github.com/houseroad/foxi"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.15)")
        replace_in_file(self, "CMakeLists.txt", "add_msvc_runtime_flag(foxi_loader)", "")
        replace_in_file(self, "CMakeLists.txt", "add_msvc_runtime_flag(foxi_dummy)", "")
        replace_in_file(self, "CMakeLists.txt", "DESTINATION lib", "RUNTIME DESTINATION bin ARCHIVE DESTINATION lib LIBRARY DESTINATION lib")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FOXI_WERROR"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # Move plugin to bin folder on Windows
        for dll_file in glob.glob(os.path.join(self.package_folder, "lib", "*.dll")):
            rename(self, src=dll_file, dst=os.path.join(self.package_folder, "bin", os.path.basename(dll_file)))

    def package_info(self):
        self.cpp_info.libs = ["foxi_dummy", "foxi_loader"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl"]
