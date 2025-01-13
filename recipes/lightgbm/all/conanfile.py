import os
from pathlib import Path

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, replace_in_file, export_conandata_patches, apply_conandata_patches
from conan.tools.scm import Version

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
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
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
        self.requires("fast_double_parser/0.7.0", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/10.1.1", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("with_openmp"):
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        if Version(self.version) >= "4.3.0":
            self.tool_requires("cmake/[>=3.18 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_STATIC_LIB"] = not self.options.shared
        tc.cache_variables["USE_DEBUG"] = self.settings.build_type in ["Debug", "RelWithDebInfo"]
        tc.cache_variables["USE_OPENMP"] = self.options.get_safe("with_openmp", False)
        tc.cache_variables["BUILD_CLI"] = False
        if is_apple_os(self):
            tc.cache_variables["APPLE_OUTPUT_DYLIB"] = True
        tc.variables["_MAJOR_VERSION"] = Version(self.version).major
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        venv = VirtualBuildEnv(self)
        venv.generate(scope="build")

    def _patch_sources(self):
        # Fix vendored dependency includes
        common_h = os.path.join(self.source_folder, "include", "LightGBM", "utils", "common.h")
        for lib in ["fmt", "fast_double_parser"]:
            replace_in_file(self, common_h, f"../../../external_libs/{lib}/include/", "")
        # Unvendor Eigen3
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "include_directories(${EIGEN_DIR})", "")
        # Avoid OpenMP_CXX_FLAGS
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")',
                        'link_libraries(OpenMP::OpenMP_CXX)')

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure(build_script_folder=Path(self.source_folder).parent)
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LightGBM")
        self.cpp_info.set_property("cmake_target_name", "LightGBM::LightGBM")
