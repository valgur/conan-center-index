import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CCTagConan(ConanFile):
    name = "cctag"
    description = "Detection of CCTag markers made up of concentric circles."
    license = "MPL-2.0"
    topics = ("cctag", "computer-vision", "detection", "image-processing",
              "markers", "fiducial-markers", "concentric-circles")
    homepage = "https://github.com/alicevision/CCTag"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "apps": [True, False],
        "serialize": [True, False],
        "visual_debug": [True, False],
        "no_cout": [True, False],
        "with_cuda": [True, False],
        "cuda_cc_list": [None, "ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "apps": False,
        "serialize": False,
        "visual_debug": False,
        "no_cout": True,
        "with_cuda": False,
        "cuda_cc_list": None, # e.g. "5.2;7.5;8.2", builds all up to 7.5 by default
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def package_id(self):
        if not self.info.options.with_cuda:
            del self.info.options.cuda_cc_list

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _boost_components(self):
        return ["atomic", "chrono", "date_time", "exception", "filesystem", "math_c99", "random", "serialization", "system", "thread", "timer"]

    @property
    def _apps_opencv_components(self):
        return ["videoio", "imgproc", "imgcodecs", "highgui"]

    def requirements(self):
        self.requires("boost/[^1.71.0]", transitive_headers=True, transitive_libs=True,
                      options={f"with_{comp.replace('_c99', '')}": True for comp in self._boost_components + ["stacktrace"]})
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("onetbb/[>=2021 <2023]")
        self.requires("opencv/[^4.5]", transitive_headers=True, transitive_libs=True,
                      options={comp: True for comp in self._apps_opencv_components} if self.options.apps else {})

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Non-core components are only used for apps
        replace_in_file(self, "CMakeLists.txt",
                        "find_package(OpenCV REQUIRED core videoio imgproc imgcodecs)",
                        "find_package(OpenCV REQUIRED core)")
        # Link to OpenCV targets
        replace_in_file(self, os.path.join("src", "CMakeLists.txt"), "${OpenCV_LIBS}", "opencv_core")
        # Cleanup RPATH if Apple in shared lib of install tree
        replace_in_file(self, "CMakeLists.txt", "SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CCTAG_SERIALIZE"] = self.options.serialize
        tc.variables["CCTAG_VISUAL_DEBUG"] = self.options.visual_debug
        tc.variables["CCTAG_NO_COUT"] = self.options.no_cout
        tc.variables["CCTAG_BUILD_APPS"] = self.options.apps
        tc.variables["CCTAG_EIGEN_NO_ALIGN"] = True
        tc.variables["CCTAG_USE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.variables["CCTAG_ENABLE_SIMD_AVX2"] = False
        tc.variables["CCTAG_BUILD_TESTS"] = False
        tc.variables["CCTAG_BUILD_DOC"] = False

        tc.variables["CCTAG_WITH_CUDA"] = self.options.with_cuda
        tc.variables["CCTAG_CUDA_CC_CURRENT_ONLY"] = False
        tc.variables["CCTAG_NVCC_WARNINGS"] = False
        if self.options.cuda_cc_list:
            tc.variables["CCTAG_CUDA_CC_LIST_INIT"] = self.options.cuda_cc_list
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CCTag")
        self.cpp_info.set_property("cmake_target_name", "CCTag::CCTag")
        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"CCTag{suffix}"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "pthread"])
        self.cpp_info.requires = [
            "eigen::eigen",
            "onetbb::onetbb",
            "opencv::opencv_core",
        ]
        self.cpp_info.requires.extend([f"boost::{comp}" for comp in self._boost_components])
        if self.options.apps:
            self.cpp_info.requires.extend([f"opencv::opencv_{comp}" for comp in self._apps_opencv_components])
        if self.settings.os == "Windows":
            self.cpp_info.requires.append("boost::stacktrace_windbg")
        else:
            self.cpp_info.requires.append("boost::stacktrace_basic")

        # CCTag links against shared CUDA runtime by default and does not use it in headers,
        # so we don't need to explicitly link against it.
