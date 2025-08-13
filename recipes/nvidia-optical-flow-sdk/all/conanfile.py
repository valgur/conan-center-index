import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NvidiaOpticalFlowSDKConan(ConanFile):
    name = "nvidia-optical-flow-sdk"
    description = ("The NVIDIA Optical Flow SDK taps in to the latest hardware capabilities of NVIDIA GPUs "
                   "dedicated to computing the relative motion of pixels between images.")
    license = "DocumentRef-LicenseAgreement.pdf:LicenseRef-Nvidia-License-Agreement"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://developer.nvidia.com/optical-flow-sdk"
    topics = ("nvidia", "optical-flow", "gpu", "computer-vision")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "archive_dir": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "archive_dir": None,
    }
    implements = ["auto_shared_fpic"]
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def package_id(self):
        del self.info.options.archive_dir

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # You can configure the compute capabilities using
        # tools.cmake.cmaketoolchain:extra_variables={"CMAKE_CUDA_ARCHITECTURES": "86-real", "CUDA_ARCH_BIN": "8.6", "CUDA_ARCH_PTX": "8.6"}
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

    def validate(self):
        check_min_cppstd(self, 11)

    @property
    def _file_name(self):
        return f"Optical_Flow_SDK{self.version}.zip"

    def validate_build(self):
        if not self.options.archive_dir:
            raise ConanInvalidConfiguration(
                f"The 'archive_dir' option must be set to a directory path where a '{self._file_name}' file is located"
            )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _source(self):
        path = os.path.join(self.options.archive_dir.value, self._file_name)
        check_sha256(self, path, self.conan_data["sources"][self.version]["sha256"])
        unzip(self, path, destination=self.source_folder, strip_root=True)

    def build(self):
        self._source()
        cmake = CMake(self)
        cmake.configure(build_script_folder="NvOFTracker")
        cmake.build()

    def package(self):
        copy(self, "LicenseAgreement.pdf", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(self, "*.h", os.path.join(self.source_folder, "NvOFTracker", "interface"), os.path.join(self.package_folder, "include"))
        copy(self, "*.h", os.path.join(self.source_folder, "NvOFFRUC", "Interface"), os.path.join(self.package_folder, "include"))
        copy(self, "*.h", os.path.join(self.source_folder, "NvOFInterface"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libs = ["nvoftracker"]
        self.cpp_info.requires = [
            "opencv::opencv_core",
            "opencv::opencv_imgproc",
            "opencv::opencv_cudaoptflow",
            "opencv::opencv_cudaimgproc",
            "opencv::opencv_cudaarithm",
        ]
        if not self.options.shared:
            self.cpp_info.system_libs.append("cudart")
            # provides a C interface
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
