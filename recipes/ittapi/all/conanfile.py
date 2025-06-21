import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class IttApiConan(ConanFile):
    name = "ittapi"
    description = (
        "The Instrumentation and Tracing Technology (ITT) API enables your application"
        " to generate and control the collection of trace data during its execution"
        " across different Intel tools."
    )
    license = "BSD-3-Clause AND GPL-2.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/intel/ittapi"
    topics = ("itt", "ittapi", "vtune", "profiler", "profiling")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "ptmark": [True, False],
    }
    default_options = {
        "fPIC": True,
        "ptmark": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        toolchain = CMakeToolchain(self)
        toolchain.variables["ITT_API_IPT_SUPPORT"] = self.options.ptmark
        toolchain.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "BSD-3-Clause.txt", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        copy(self, "GPL-2.0-only.txt", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        # https://github.com/intel/ittapi/blob/03f7260c96d4b437d12dceee7955ebb1e30e85ad/CMakeLists.txt#L176
        self.cpp_info.set_property("cmake_file_name", "ittapi")
        self.cpp_info.set_property("cmake_target_name", "ittapi::ittnotify")
        self.cpp_info.set_property("cmake_target_aliases", ["ittapi::ittapi"]) # for compatibility with earlier revisions of the recipe
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["libittnotify"]
        else:
            self.cpp_info.libs = ["ittnotify"]
            self.cpp_info.system_libs = ["dl"]
