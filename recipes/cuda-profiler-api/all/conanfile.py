import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudaProfilerApiConan(ConanFile):
    name = "cuda-profiler-api"
    description = "CUDA Profiler API Headers"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html#range-replay-define-range"
    topics = ("cuda", "profiler")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        v = Version(self.version)
        self.requires(f"cudart/[~{v.major}.{v.minor}]")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_profiler_api", platform_id="linux-x86_64")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
