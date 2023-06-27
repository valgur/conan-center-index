# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class Nmslib(ConanFile):
    name = "nmslib"
    description = (
        "Non-Metric Space Library (NMSLIB): An efficient similarity search library "
        "and a toolkit for evaluation of k-NN methods for generic non-metric spaces."
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/nmslib/nmslib"
    topics = ("knn-search", "non-metric", "neighborhood-graphs", "neighborhood-graphs", "vp-tree")

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if is_msvc(self):
            if self.settings.compiler.version == "14":
                raise ConanInvalidConfiguration(
                    "Visual Studio 14 builds are not supported"
                )  # TODO: add reason in message
            if self.options.shared:
                raise ConanInvalidConfiguration(
                    "Visual Studio shared builds are not supported (.lib artifacts missing)"
                )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["WITHOUT_TESTS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder="similarity_search")
        cmake.build()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["NonMetricSpaceLib"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread"]
