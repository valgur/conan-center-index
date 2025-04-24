import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
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
        "source": ["ANY"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "source": "",
    }
    implements = ["auto_shared_fpic"]
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opencv/4.11.0", options={
            "cudaoptflow": True,
            "cudaarithm": True,
            "cudaimgproc": True,
            "cudawarping": True,
            "optflow": True,
            "with_cuda": True,
            "ximgproc": True,
            "dnn": False,
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

    def build(self):
        check_sha256(self, str(self.options.source), self.conan_data["sources"][self.version]["sha256"])
        unzip(self, str(self.options.source), destination=self.source_folder, strip_root=True)
        save(self, os.path.join(self.source_folder, "NvOFTracker", "NvOFTSample", "CMakeLists.txt"), "")
        replace_in_file(self, os.path.join(self.source_folder, "NvOFTracker", "CMakeLists.txt"),
                        "install (TARGETS NvOFTSample RUNTIME DESTINATION bin)", "")
        cmake = CMake(self)
        cmake.configure(build_script_folder="NvOFTracker")
        cmake.build()

    def package(self):
        copy(self, "LicenseAgreement.pdf", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["nvoftracker"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")
