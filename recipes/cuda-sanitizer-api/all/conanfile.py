import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CudaSanitizerApiConan(ConanFile):
    name = "cuda-sanitizer-api"
    description = "Provides a set of APIs to enable third party tools to write GPU sanitizing tools"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/compute-sanitizer/SanitizerApiGuide/"
    topics = ("cuda", "sanitizer")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("libvdpau/[^1.5]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_sanitizer_api")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_sanitizer_api", platform_id="linux-x86_64")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        source_folder = os.path.join(self.source_folder, "compute-sanitizer")
        copy(self, "*", os.path.join(source_folder, "include"), os.path.join(self.package_folder, "include"))
        rmdir(self, os.path.join(source_folder, "include"))
        rmdir(self, os.path.join(source_folder, "docs"))
        rmdir(self, os.path.join(source_folder, "x86"))
        if self.settings.os == "Linux":
            copy(self, "*.so", source_folder, os.path.join(self.package_folder, "lib"))
            copy(self, "*", source_folder, os.path.join(self.package_folder, "bin"), excludes="*.so")
        else:
            copy(self, "*.lib", source_folder, os.path.join(self.package_folder, "lib"))
            copy(self, "*", source_folder, os.path.join(self.package_folder, "bin"), excludes="*.lib")

    def package_info(self):
        self.cpp_info.libs = ["sanitizer-public"]
