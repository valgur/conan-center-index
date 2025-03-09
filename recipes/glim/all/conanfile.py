import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, rmdir, copy, replace_in_file

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

    def configure(self):
        # Make OpenCV a bit more lightweight
        self.options["opencv"].with_ffmpeg = False
        self.options["opencv"].with_tesseract = False

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.86.0", transitive_headers=True, force=True)
        self.requires("eigen/3.4.0", transitive_headers=True, transitive_libs=True)
        self.requires("opencv/4.11.0", transitive_headers=True, transitive_libs=True)
        self.requires("gtsam/4.2", transitive_headers=True, transitive_libs=True)
        self.requires("gtsam_points/1.0.6", transitive_headers=True, transitive_libs=True, options={"cuda": self.options.cuda})
        self.requires("nlohmann_json/3.11.3", transitive_headers=True, transitive_libs=True)
        self.requires("openmp/system")
        self.requires("spdlog/1.14.1", transitive_headers=True, transitive_libs=True)
        if self.options.viewer:
            self.requires("iridescence/0.1.3", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

        if self.options.cuda and not self.dependencies["gtsam_points"].options.cuda:
            raise ConanInvalidConfiguration("-o glim/*:cuda=True requires -o gtsam_points/*:cuda=True")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

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
        # Make sure third-party deps are unvendored
        rmdir(self, os.path.join(self.source_folder, "thirdparty"))
        # Forbid building as a ROS package with ROS deps
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "DEFINED ENV{ROS_VERSION}", "FALSE")
        # Avoid overlinking of OpenCV
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "${OpenCV_LIBRARIES}", "opencv_core")

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

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "glim")
        self.cpp_info.set_property("cmake_target_name", "glim::_glim_all")

        def _add_component(name, reqs=None):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", f"glim::{name}")
            component.libs = [name]
            component.requires = reqs or []
            if name != "glim":
                component.requires.append("glim")

        main_reqs = [
            "boost::headers",
            "boost::serialization",
            "eigen::eigen",
            "gtsam::gtsam",
            "gtsam_points::gtsam_points",
            "nlohmann_json::nlohmann_json",
            "opencv::opencv_core",
            "openmp::openmp",
            "spdlog::spdlog",
        ]

        _add_component("glim", main_reqs)
        _add_component("global_mapping")
        _add_component("global_mapping_pose_graph")
        _add_component("odometry_estimation_cpu")
        _add_component("odometry_estimation_ct")
        _add_component("sub_mapping")
        _add_component("sub_mapping_passthrough")

        if self.options.cuda:
            # CUDA dependency is provided via gtsam_points
            _add_component("odometry_estimation_gpu")

        if self.options.viewer:
            _add_component("interactive_viewer", ["iridescence::iridescence"])
            _add_component("standard_viewer", ["iridescence::iridescence"])
            _add_component("memory_monitor", ["iridescence::iridescence"])
