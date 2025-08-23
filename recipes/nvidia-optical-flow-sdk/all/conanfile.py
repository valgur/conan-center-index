import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvidiaOpticalFlowSDKConan(ConanFile):
    name = "nvidia-optical-flow-sdk"
    description = ("The NVIDIA Optical Flow SDK taps in to the latest hardware capabilities of NVIDIA GPUs "
                   "dedicated to computing the relative motion of pixels between images.")
    license = "MIT"  # BSD-3-Clause for v2 and v1
    homepage = "https://developer.nvidia.com/optical-flow-sdk"
    topics = ("nvidia", "optical-flow", "gpu", "computer-vision")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "nvoffruc": [True, False],
        "nvoftracker": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "nvoffruc": False,  # not MIT-licensed
        "nvoftracker": False,  # not MIT-licensed
    }
    options_description = {
        "nvoffruc": "Install NVIDIA Optical Flow and Frame Rate Up-Conversion (NvOFFRUC) headers",
        "nvoftracker": "Build and isntall the NvOFTracker library",
    }
    implements = ["auto_shared_fpic"]
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "3.0":
            self.license = "BSD-3-Clause"
            del self.options.nvoffruc
            del self.options.nvoftracker

    def configure(self):
        if self.options.get_safe("nvoftracker"):
            self.package_type = "library"
        else:
            self.options.rm_safe("shared")
            self.options.rm_safe("fPIC")
        if self.options.get_safe("shared"):
            self.options.rm_safe("fPIC")
        if self.options.get_safe("nvoffruc") or self.options.get_safe("nvoftracker"):
            self.license += " AND DocumentRef-LicenseAgreement.pdf:LicenseRef-Nvidia-License-Agreement"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("nvoftracker"):
            self.requires("opencv/[^4.5]", options={
                "cudaoptflow": True,
                "cudaarithm": True,
                "cudaimgproc": True,
                "cudawarping": True,
                "highgui": True,
                "optflow": True,
                "ximgproc": True,
                "with_cuda": True,
            })

    @property
    def _file_name(self):
        if Version(self.version) >= "5.0":
            return f"Optical_Flow_SDK{self.version}.zip"
        else:
            return f"Optical_Flow_SDK_{self.version}.zip"

    @property
    def _archive_dir(self):
        return self.conf.get("user.tools:offline_archives_folder", check_type=str, default=None)

    def validate_build(self):
        if not self._archive_dir:
            raise ConanInvalidConfiguration(f"user.tools:offline_archives_folder config variable must be set"
                                            f" to a location containing a {self._file_name} archive file.")
        if self.options.get_safe("nvoftracker"):
            check_min_cppstd(self, 11)

    def source(self):
        if Version(self.version) < "3.0":
            get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _source_sdk(self):
        path = os.path.join(self._archive_dir, self._file_name)
        check_sha256(self, path, self.conan_data["sources"][self.version]["sha256"])
        unzip(self, path, destination=self.source_folder, strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if self.options.get_safe("nvoftracker"):
            tc = CMakeToolchain(self)
            tc.generate()
            deps = CMakeDeps(self)
            deps.generate()

    def build(self):
        if Version(self.version) >= "3.0":
            self._source_sdk()
        if self.options.get_safe("nvoftracker"):
            cmake = CMake(self)
            cmake.configure(build_script_folder="NvOFTracker")
            cmake.build()

    def _extract_header_license(self):
        content = Path(self.package_folder, "include", "nvOpticalFlowCommon.h").read_text(encoding="utf-8")
        license = content.split("*/", 1)[0].replace("/*", "").replace("* ", "").replace("*", "")
        license = license.split("this header file only:\n")[-1].strip()
        licenses_dir = Path(self.package_folder, "licenses")
        licenses_dir.mkdir()
        Path(licenses_dir, "LICENSE").write_text(license, encoding="utf-8")

    def package(self):
        if Version(self.version) >= "3.0":
            copy(self, "*.h", os.path.join(self.source_folder, "NvOFInterface"), os.path.join(self.package_folder, "include"))
            if self.options.get_safe("nvoftracker") or self.options.get_safe("nvoffruc"):
                copy(self, "LicenseAgreement.pdf", self.source_folder, os.path.join(self.package_folder, "licenses"))
            if self.options.get_safe("nvoffruc"):
                copy(self, "*.h", os.path.join(self.source_folder, "NvOFFRUC", "Interface"), os.path.join(self.package_folder, "include"))
            if self.options.get_safe("nvoftracker"):
                cmake = CMake(self)
                cmake.install()
                copy(self, "*.h", os.path.join(self.source_folder, "NvOFTracker", "interface"), os.path.join(self.package_folder, "include"))
        else:
            copy(self, "*.h", self.source_folder, os.path.join(self.package_folder, "include"))
        self._extract_header_license()

    def package_info(self):
        # The CMake names are unofficial
        self.cpp_info.set_property("cmake_file_name", "nvof")
        self.cpp_info.set_property("cmake_target_name", "nvof::nvof")

        if self.options.get_safe("nvoftracker"):
            self.cpp_info.components["nvoftracker"].set_property("cmake_target_name", "nvof::nvoftracker")
            self.cpp_info.components["nvoftracker"].libs = ["nvoftracker"]
            self.cpp_info.components["nvoftracker"].requires = [
                "opencv::opencv_core",
                "opencv::opencv_imgproc",
                "opencv::opencv_cudaoptflow",
                "opencv::opencv_cudaimgproc",
                "opencv::opencv_cudaarithm",
            ]
            if not self.options.shared:
                # provides a C interface
                libcxx = stdcpp_library(self)
                if libcxx:
                    self.cpp_info.components["nvoftracker"].system_libs.append(libcxx)
            if self.settings.os == "Linux":
                self.cpp_info.components["nvoftracker"].system_libs.append("m")
        else:
            self.cpp_info.libdirs = []
            self.cpp_info.bindirs = []
