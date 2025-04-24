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
        "source": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "source": "",
    }
    implements = ["auto_shared_fpic"]
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def package_id(self):
        del self.info.options.source

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
        if not self.options.source:
            raise ConanInvalidConfiguration(
                f"The 'source' option must be a valid path to the Optical_Flow_SDK{self.version}.zip source archive file"
            )
        check_min_cppstd(self, 11)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _source(self):
        check_sha256(self, str(self.options.source), self.conan_data["sources"][self.version]["sha256"])
        unzip(self, str(self.options.source), destination=self.source_folder, strip_root=True)
        apply_conandata_patches(self)

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
