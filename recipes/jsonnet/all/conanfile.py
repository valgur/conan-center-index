# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, cross_building, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class JsonnetConan(ConanFile):
    name = "jsonnet"
    description = "Jsonnet - The data templating language"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/jsonnet"
    topics = ("config", "json", "functional", "configuration")

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
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            # This is a workround.
            # If jsonnet is shared, rapidyaml must be built as shared,
            # or the c4core functions that rapidyaml depends on will not be able to be found.
            # This seems to be a issue of rapidyaml.
            # https://github.com/conan-io/conan-center-index/pull/9786#discussion_r829887879
            if Version(self.version) >= "0.18.0":
                self.options["rapidyaml"].shared = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("nlohmann_json/3.10.5")
        if Version(self.version) >= "0.18.0":
            self.requires("rapidyaml/0.4.1")

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self, skip_x64_x86=True):
            raise ConanInvalidConfiguration("jsonnet does not support cross building")

        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "11")

        if self.options.shared and is_msvc(self) and "d" in msvc_runtime_flag(self):
            raise ConanInvalidConfiguration(
                "shared {} is not supported with MTd/MDd runtime".format(self.name)
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["BUILD_SHARED_BINARIES"] = False
        tc.variables["BUILD_JSONNET"] = False
        tc.variables["BUILD_JSONNETFMT"] = False
        tc.variables["USE_SYSTEM_JSON"] = True
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["libjsonnet"].libs = ["jsonnet"]
        self.cpp_info.components["libjsonnet"].requires = ["nlohmann_json::nlohmann_json"]
        if Version(self.version) >= "0.18.0":
            self.cpp_info.components["libjsonnet"].requires.append("rapidyaml::rapidyaml")

        if stdcpp_library(self):
            self.cpp_info.components["libjsonnet"].system_libs.append(stdcpp_library(self))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libjsonnet"].system_libs.append("m")

        self.cpp_info.components["libjsonnetpp"].libs = ["jsonnet++"]
        self.cpp_info.components["libjsonnetpp"].requires = ["libjsonnet"]
