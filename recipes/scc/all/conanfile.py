# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class SystemcComponentsConan(ConanFile):
    name = "scc"
    description = "A light weight productivity library for SystemC and TLM 2.0"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://minres.github.io/SystemC-Components"
    topics = ("systemc", "modeling", "tlm", "scc")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_phase_callbacks": [True, False],
        "enable_phase_callbacks_tracing": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_phase_callbacks": False,
        "enable_phase_callbacks_tracing": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.settings.os == "Macos":
            raise ConanInvalidConfiguration(f"{self.name} is not suppported on {self.settings.os}.")
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "7":
            raise ConanInvalidConfiguration("GCC < version 7 is not supported")

    def build_requirements(self):
        self.tool_requires("cmake/3.24.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SC_WITH_PHASE_CALLBACKS"] = self.options.enable_phase_callbacks
        tc.variables["SC_WITH_PHASE_CALLBACK_TRACING"] = self.options.enable_phase_callbacks_tracing
        tc.variables["BUILD_SCC_DOCUMENTATION"] = False
        tc.variables["SCC_LIB_ONLY"] = True
        if self.settings.os == "Windows":
            tc.variables["SCC_LIMIT_TRACE_TYPE_LIST"] = True

    def build(self):
        cmake = CMake(self)

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["busses"].libs = ["busses"]
        self.cpp_info.components["scc-sysc"].libs = ["scc-sysc"]
        self.cpp_info.components["scc-util"].libs = ["scc-util"]
        self.cpp_info.components["scv-tr"].libs = ["scv-tr"]
        self.cpp_info.components["tlm-interfaces"].libs = ["tlm-interfaces"]
