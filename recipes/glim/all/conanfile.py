import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class GlimPackage(ConanFile):
    name = "glim"
    description = "GLIM: versatile and extensible range-based 3D localization and mapping framework"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/koide3/glim"
    topics = ("localization", "mapping", "gpu", "ros", "imu", "lidar", "slam", "3d", "rgb-d")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "march_native": [True, False],
        "cuda": [True, False],
        "viewer": [True, False],
    }
    default_options = {
        "march_native": False,
        "cuda": False,
        "viewer": True,
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
            "Visual Studio": "16",
            "msvc": "192",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.85.0", transitive_headers=True, force=True)
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("opencv/4.9.0", transitive_headers=True, transitive_libs=True)
        self.requires("gtsam/4.2", transitive_headers=True, transitive_libs=True)
        self.requires("gtsam_points/1.0.2", transitive_headers=True, transitive_libs=True, options={"cuda": self.options.cuda})
        self.requires("nlohmann_json/3.11.3", transitive_headers=True)
        self.requires("openmp/system")
        self.requires("spdlog/1.14.1", transitive_headers=True)
        if self.options.viewer:
            self.requires("iridescence/cci.20240709", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        if self.options.cuda and not self.dependencies["gtsam_points"].options.cuda:
            raise ConanInvalidConfiguration("-o glim/*:cuda=True requires -o gtsam_points/*:cuda=True")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_WITH_MARCH_NATIVE"] = self.options.march_native
        tc.variables["BUILD_WITH_CUDA"] = self.options.cuda
        tc.variables["BUILD_WITH_VIEWER"] = self.options.viewer
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("gtsam", "cmake_target_name", "GTSAM::GTSAM")
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        rmdir(self, os.path.join(self.source_folder, "thirdparty"))

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "glim")
        self.cpp_info.set_property("cmake_target_name", "glim::glim")

        self.cpp_info.libs = [
            "glim",
            "global_mapping",
            "global_mapping_pose_graph",
            "odometry_estimation_cpu",
            "odometry_estimation_ct",
            "sub_mapping",
            "sub_mapping_passthrough",
        ]
        if self.options.cuda:
            self.cpp_info.libs += [
                "odometry_estimation_gpu",
            ]
        if self.options.viewer:
            self.cpp_info.libs += [
                "interactive_viewer",
                "standard_viewer",
            ]
