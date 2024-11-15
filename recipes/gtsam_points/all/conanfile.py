import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, rmdir, rm, copy
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class GtsamPointsPackage(ConanFile):
    name = "gtsam_points"
    description = "A collection of GTSAM factors and optimizers for range-based SLAM"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/koide3/gtsam_points"
    topics = ("localization", "mapping", "gpu", "cuda", "point-cloud", "registration", "slam", "factor-graph")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "march_native": [True, False],
        "cuda": [True, False],
    }
    default_options = {
        "march_native": False,
        "cuda": False,
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "9",
            "clang": "10",
            "apple-clang": "12",
            "msvc": "192",
        }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan-cuda-wrapper.cmake", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.86.0", transitive_headers=True, transitive_libs=True, force=True)
        self.requires("eigen/3.4.0", transitive_headers=True, transitive_libs=True)
        self.requires("gtsam/4.2", transitive_headers=True, transitive_libs=True)
        self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        self.requires("nanoflann/1.3.2", transitive_headers=True, transitive_libs=True)
        if self.options.cuda:
            # Thrust 2.x from CUDA 12 and newer is not compatible
            self.requires("thrust/1.17.2", transitive_headers=True, transitive_libs=True, options={"device_system": "cuda"})

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_WITH_MARCH_NATIVE"] = self.options.march_native
        tc.variables["BUILD_WITH_CUDA"] = self.options.cuda
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("gtsam", "cmake_target_name", "GTSAM::GTSAM")
        deps.generate()

        VirtualBuildEnv(self).generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        rmdir(self, os.path.join(self.source_folder, "thirdparty"))
        rm(self, "FindGTSAM.cmake", os.path.join(self.source_folder, "cmake"))

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        if self.options.cuda:
            copy(self, "conan-cuda-wrapper.cmake", self.export_sources_folder, os.path.join(self.package_folder, "lib", "cmake", "gtsam_points"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "gtsam_points")

        self.cpp_info.components["libgtsam_points"].set_property("cmake_target_name", "gtsam_points::gtsam_points")
        self.cpp_info.components["libgtsam_points"].libs = ["gtsam_points"]
        requires = [
            "boost::headers",
            "boost::filesystem",
            "eigen::eigen",
            "gtsam::gtsam",
            "openmp::openmp",
            "nanoflann::nanoflann",
        ]
        self.cpp_info.components["libgtsam_points"].requires += requires

        if self.options.cuda:
            self.cpp_info.components["libgtsam_points_cuda"].set_property("cmake_target_name", "gtsam_points::gtsam_points_cuda")
            self.cpp_info.components["libgtsam_points_cuda"].libs = ["gtsam_points_cuda"]
            self.cpp_info.components["libgtsam_points_cuda"].requires += requires
            self.cpp_info.components["libgtsam_points_cuda"].requires.append("thrust::thrust")
            self.cpp_info.components["libgtsam_points"].requires.append("libgtsam_points_cuda")

            # Add cudart dependency
            cmake_module_dir = os.path.join("lib", "cmake", "gtsam_points")
            self.cpp_info.builddirs.append(cmake_module_dir)
            self.cpp_info.set_property("cmake_build_modules", [os.path.join(cmake_module_dir, "conan-cuda-wrapper.cmake")])
