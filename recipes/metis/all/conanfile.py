# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches
from conan.tools.files import copy, export_conandata_patches, get
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class METISConan(ConanFile):
    name = "metis"
    description = (
        "set of serial programs for partitioning graphs,"
        " partitioning finite element meshes, and producing"
        " fill reducing orderings for sparse matrices"
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/KarypisLab/METIS"
    topics = ("karypislab", "graph", "partitioning-algorithms")

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
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gklib/5.1.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.variables["SHARED"] = self.options.shared
        tc.variables["METIS_INSTALL"] = True
        tc.variables["ASSERT"] = self.settings.build_type == "Debug"
        tc.variables["ASSERT2"] = self.settings.build_type == "Debug"
        tc.variables["METIS_IDX64"] = True
        tc.variables["METIS_REAL64"] = True
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.libs = ["metis"]
        self.cpp_info.requires.append("gklib::gklib")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
        if is_msvc(self) or self._is_mingw:
            self.cpp_info.defines.append("USE_GKREGEX")
        if is_msvc(self):
            self.cpp_info.defines.append("__thread=__declspec(thread)")
