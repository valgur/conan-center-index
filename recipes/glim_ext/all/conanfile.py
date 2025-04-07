import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GlimExtPackage(ConanFile):
    name = "glim_ext"
    description = "glim_ext is a set of extension modules for GLIM, a 3D LiDAR mapping framework."
    license = ""
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/koide3/glim_ext"
    topics = ("localization", "mapping", "gpu", "ros", "imu", "lidar", "slam", "3d", "rgb-d")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "velsupp": [True, False],
        "imuval": [True, False],
        "flatearther": [True, False],
        "dbow": [True, False],
        # TODO:
        # "scan_context": [True, False],
        # "orbslam": [True, False],
    }
    default_options = {
        "velsupp": True,
        "imuval": True,
        "flatearther": True,
        "dbow": False,
        # "scan_context": True,
        # "orbslam": True,
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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("glim/1.0.4", transitive_headers=True, transitive_libs=True)
        # Most dependencies are available transitively through glim
        if self.options.imuval:
            self.requires("iridescence/0.1.3")
            self.requires("implot/0.16")
        # TODO: add ScanContext for scan_context
        # TODO: add ORB_SLAM3 for orbslam
        # TODO: unvendor DBow2 and DBow3

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_ORBSLAM"] = False  # self.options.orbslam
        tc.variables["ENABLE_VELSUPP"] = self.options.velsupp
        tc.variables["ENABLE_IMUVAL"] = self.options.imuval
        tc.variables["ENABLE_SCAN_CONTEXT"] = False  # self.options.scan_context
        tc.variables["ENABLE_DBOW"] = self.options.dbow
        tc.variables["ENABLE_GNSS"] = False  # Requires ROS1 or ROS2
        tc.variables["ENABLE_FLATEARTHER"] = self.options.flatearther
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("gtsam", "cmake_target_name", "GTSAM::GTSAM")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libs = ["glim_ext", "glim_callback_demo"]

        if self.options.velsupp:
            self.cpp_info.libs.append("velocity_suppressor")
        if self.options.imuval:
            self.cpp_info.libs.append("imu_validator")
        if self.options.flatearther:
            self.cpp_info.libs.append("flat_earther")
        if self.options.dbow:
            self.cpp_info.libs.append("dbow_loop_detector")
        # if self.options.scan_context:
        #     self.cpp_info.libs.append("scan_context_loop_detector")
        # if self.options.orbslam:
        #     self.cpp_info.libs.append("orb_slam_odometry")
