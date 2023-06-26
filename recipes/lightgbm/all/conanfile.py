# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class LightGBMConan(ConanFile):
    name = "lightgbm"
    description = (
        "A fast, distributed, high performance gradient boosting "
        "(GBT, GBDT, GBRT, GBM or MART) framework based on decision tree algorithms, "
        "used for ranking, classification and many other machine learning tasks."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/LightGBM"
    topics = ("machine-learning", "boosting")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
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

    def requirements(self):
        self.requires("eigen/3.4.0")
        self.requires("fast_double_parser/0.6.0")
        self.requires("fmt/9.0.0")
        if self.options.with_openmp and self.settings.compiler in ("clang", "apple-clang"):
            self.requires("llvm-openmp/11.1.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC_LIB"] = not self.options.shared
        tc.variables["USE_DEBUG"] = self.settings.build_type == "Debug"
        tc.variables["USE_OPENMP"] = self.options.with_openmp
        if self.settings.os == "Macos":
            tc.variables["APPLE_OUTPUT_DYLIB"] = True
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LightGBM")
        self.cpp_info.set_property("cmake_target_name", "LightGBM::LightGBM")

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.names["cmake_find_package"] = "LightGBM"
        self.cpp_info.names["cmake_find_package_multi"] = "LightGBM"

        self.cpp_info.libs = ["lib_lightgbm"] if is_msvc(self) else ["_lightgbm"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi"])
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs.append("pthread")
        if not self.options.shared and self.options.with_openmp:
            if is_msvc(self):
                openmp_flags = ["-openmp"]
            elif self.settings.compiler == "gcc":
                openmp_flags = ["-fopenmp"]
            elif self.settings.compiler in ("clang", "apple-clang"):
                openmp_flags = ["-Xpreprocessor", "-fopenmp"]
            else:
                openmp_flags = []
            self.cpp_info.exelinkflags.extend(openmp_flags)
            self.cpp_info.sharedlinkflags.extend(openmp_flags)
