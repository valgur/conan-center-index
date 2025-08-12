import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

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
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

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

    @property
    def _external_nvvm(self):
        return Version(self.version) >= "13.0"

    def package(self):
        host_folder = os.path.join(self.source_folder, "host")
        self._utils.download_cuda_package(self, "cuda_nvcc", scope="host", destination=host_folder)
        if self._external_nvvm:
            # using nvvm via a separate Conan package almost works, but device code LTO fails in mathdx with
            # nvlink fatal   : elfLink linker library load error
            # bundling nvvm back into nvcc for this reason.
            self._utils.download_cuda_package(self, "libnvvm", scope="host", destination=host_folder)
        if self._cross_toolchain:
            target_folder = os.path.join(self.source_folder, "target")
            self._utils.download_cuda_package(self, "cuda_nvcc", scope="target", destination=target_folder)
            if self._external_nvvm:
                self._utils.download_cuda_package(self, "libnvvm", scope="target", destination=target_folder)
        else:
            target_folder = host_folder
        copy(self, "LICENSE", host_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(host_folder, "bin"), os.path.join(self.package_folder, "bin"))
        copy(self, "*", os.path.join(host_folder, "include"), os.path.join(self.package_folder, "include"))
        if Version(self.version) < "13.0":
            # remove nvptxcompiler_static and cuda-crt files
            rm(self, "nvPTXCompiler.h", os.path.join(self.package_folder, "include"))
            rmdir(self, os.path.join(self.package_folder, "include", "crt"))
        copy(self, "*", os.path.join(target_folder, "nvvm"), os.path.join(self.package_folder, "nvvm"))
        copy(self, "cicc*", os.path.join(host_folder, "nvvm", "bin"), os.path.join(self.package_folder, "nvvm", "bin"))

    def package_info(self):
        ext = ".exe" if self.settings.os == "Windows" else ""
        nvcc = os.path.join(self.package_folder, "bin", "nvcc" + ext)
        self.conf_info.update("tools.build:compiler_executables", {"cuda": nvcc})
        self.runenv_info.define_path("CUDACXX", nvcc)
        self.runenv_info.define_path("CUDA_PATH", os.path.join(self.package_folder, "bin"))
