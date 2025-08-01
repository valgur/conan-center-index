import json
import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvccConan(ConanFile):
    name = "nvcc"
    description = "Compiler for CUDA applications"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "nvcc")
    package_type = "application"
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

    @property
    def _cross_toolchain(self):
        return self.settings_target and self.settings.arch != self.settings_target.arch

    @property
    def _host_platform_id(self):
        return self._utils.cuda_platform_id(self.settings)

    @property
    def _target_platform_id(self):
        return self._utils.cuda_platform_id(self.settings_target)

    def validate(self):
        if self._host_platform_id is None:
            raise ConanInvalidConfiguration(f"Unsupported platform: {self.settings.os}/{self.settings.arch}")
        if self._cross_toolchain:
            if self.settings.os != self.settings_target.os:
                raise ConanInvalidConfiguration("Host and target OS-s must match")
            if self._target_platform_id is None:
                raise ConanInvalidConfiguration(f"Unsupported cross-compilation arch: {self.settings.arch}")
        self._utils.validate_cuda(self)

    @cached_property
    def _redist_info(self):
        package_name = "cuda_nvcc"
        download(self, **self.conan_data["sources"][self.version], filename=os.path.join(self.build_folder, "redistrib.json"))
        redist_info = json.loads(load(self, "redistrib.json"))[package_name]
        assert redist_info["version"] == self.version
        return redist_info

    def package(self):
        package_info = self._redist_info[self._host_platform_id]
        url = "https://developer.download.nvidia.com/compute/cuda/redist/" + package_info["relative_path"]
        host_folder = os.path.join(self.package_folder, "host")
        get(self, url, sha256=package_info["sha256"], strip_root=True, destination=host_folder)
        if self._cross_toolchain:
            package_info = self._redist_info[self._target_platform_id]
            url = "https://developer.download.nvidia.com/compute/cuda/redist/" + package_info["relative_path"]
            target_folder = os.path.join(self.build_folder, "target")
            get(self, url, sha256=package_info["sha256"], strip_root=True, destination=target_folder)
        else:
            target_folder = host_folder
        copy(self, "LICENSE", host_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(host_folder, "bin"), os.path.join(self.package_folder, "bin"))
        # nvptxcompiler_static is packaged separately, don't copy lib/
        copy(self, "*", os.path.join(target_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(target_folder, "nvvm"), os.path.join(self.package_folder, "nvvm"))
        copy(self, "cicc*", os.path.join(host_folder, "nvvm", "bin"), os.path.join(self.package_folder, "nvvm", "bin"))

    def package_info(self):
        ext = ".exe" if self.settings.os == "Windows" else ""
        nvcc = os.path.join(self.package_folder, "bin", "nvcc" + ext)
        self.conf_info.update("tools.build:compiler_executables", {"cuda": nvcc})
        self.runenv_info.define_path("CUDACXX", nvcc)
