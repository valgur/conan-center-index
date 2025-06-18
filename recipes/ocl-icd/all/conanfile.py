import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class OclIcdConan(ConanFile):
    name = "ocl-icd"
    description = "OpenCL generic Installable Client Driver support"
    license = "BSD-2-Clause"
    homepage = "https://github.com/OCL-dev/ocl-icd"
    topics = ("opencl",)
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    languages = ["C"]
    options = {
        "header_only": [True, False],
    }
    default_options = {
        "header_only": False,
    }
    implements = ["auto_header_only"]

    def configure(self):
        if self.options.header_only:
            self.package_type = "header-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opencl-headers/[*]", transitive_headers=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Only Linux is supported")

    def build_requirements(self):
        self.tool_requires("libtool/[^2.4.7]")
        if not shutil.which("ruby"):
            self.tool_requires("ruby/[^3.1.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")
        tc = AutotoolsToolchain(self)
        if not self.options.header_only:
            tc.configure_args.append("--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug")
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        if self.options.header_only:
            autotools.make(target="ocl_icd.h")
        else:
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if self.options.header_only:
            copy(self, "ocl_icd.h", self.build_folder, os.path.join(self.package_folder, "include"))
            return
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.components["ocl-icd_"].set_property("pkg_config_name", "ocl-icd")
        self.cpp_info.components["ocl-icd_"].includedirs = ["include"]
        self.cpp_info.components["ocl-icd_"].libdirs = []
        self.cpp_info.components["ocl-icd_"].bindirs = []
        self.cpp_info.components["ocl-icd_"].requires = ["opencl-headers::opencl-headers"]

        if not self.options.header_only:
            self.cpp_info.components["OpenCL"].set_property("pkg_config_name", "OpenCL")
            self.cpp_info.components["OpenCL"].libs = ["OpenCL"]
            self.cpp_info.components["OpenCL"].includedirs = []
            self.cpp_info.components["OpenCL"].requires = ["opencl-headers::opencl-headers"]
            self.cpp_info.components["OpenCL"].system_libs = ["dl"]
