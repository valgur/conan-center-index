import json
import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvccHeadersConan(ConanFile):
    name = "nvcc-headers"
    description = "Header files for the CUDA NVCC compiler"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "nvcc")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @property
    def _platform_id(self):
        if self.settings.get_safe("cuda.platform") == "sbsa":
            if self.settings.os != "Linux" or self.settings.arch != "armv8":
                raise ConanInvalidConfiguration(f"Invalid OS/arch combination for cuda.platform=sbsa: {self.settings.os}/{self.settings.arch}")
            return "linux-sbsa"
        return {
            ("Windows", "x86_64"): "windows-x86_64",
            ("Linux", "x86_64"): "linux-x86_64",
            ("Linux", "armv8"): "linux-aarch64",
        }.get((str(self.settings.os), str(self.settings.arch)))

    def validate(self):
        if self._platform_id is None:
            raise ConanInvalidConfiguration(f"Unsupported platform: {self.settings.os}/{self.settings.arch}")

    @cached_property
    def _redist_info(self):
        package_name = "cuda_nvcc"
        download(self, **self.conan_data["sources"][self.version], filename=os.path.join(self.build_folder, "redistrib.json"))
        redist_info = json.loads(load(self, "redistrib.json"))[package_name]
        assert redist_info["version"] == self.version
        return redist_info

    def package(self):
        package_info = self._redist_info[self._platform_id]
        url = "https://developer.download.nvidia.com/compute/cuda/redist/" + package_info["relative_path"]
        get(self, url, sha256=package_info["sha256"], strip_root=True, destination=self.build_folder)
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "include"), os.path.join(self.package_folder, "include"), excludes="nvPTXCompiler.h")

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
