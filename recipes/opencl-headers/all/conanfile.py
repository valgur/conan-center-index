from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=2.1"


class OpenclHeadersConan(ConanFile):
    name = "opencl-headers"
    description = "C language headers for the OpenCL API"
    license = "Apache-2.0"
    topics = ("opencl", "header-only", "api-headers")
    homepage = "https://github.com/KhronosGroup/OpenCL-Headers"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _target_name(self):
        return "OpenCL::Headers"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*", src=os.path.join(self.source_folder, "CL"), dst=os.path.join(self.package_folder, "include", "CL"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenCLHeaders")
        self.cpp_info.set_property("cmake_target_name", self._target_name)
        self.cpp_info.set_property("pkg_config_name", "OpenCL-Headers")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
