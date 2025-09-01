import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvvmConan(ConanFile):
    name = "nvvm"
    description = "NVVM: an optimizing compiler library that generates PTX from NVVM intermediate representation (IR)."
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/nvvm-ir-spec/"
    topics = ("cuda", "nvcc", "compiler", "intermediate-representation")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "target_arch": [None, "aarch64", "ppc64le", "sbsa", "x86_64"],
    }
    default_options = {
        "target_arch": None,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    @property
    def _host_platform_id(self):
        return self.cuda.get_platform_id(self.settings)

    @property
    def _target_platform_id(self):
        return self.cuda.get_platform_id(self.settings_target)

    @property
    def _cross_toolchain(self):
        return self.settings_target and self.settings.arch != self.settings_target.arch

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def validate(self):
        if self._host_platform_id is None:
            raise ConanInvalidConfiguration(f"Unsupported platform: {self.settings.os}/{self.settings.arch}")
        if self._cross_toolchain:
            if self.settings.os != self.settings_target.os:
                raise ConanInvalidConfiguration("Host and target OS-s must match")
            if self._target_platform_id is None:
                raise ConanInvalidConfiguration(f"Unsupported cross-compilation arch: {self.settings.arch}")

    def package(self):
        pkg = "libnvvm" if Version(self.version) >= "13.0" else "cuda_nvcc"
        host_folder = os.path.join(self.source_folder, "host")
        self.cuda.download_package(pkg, scope="host", destination=host_folder)
        if self._cross_toolchain:
            target_folder = os.path.join(self.source_folder, "target")
            self.cuda.download_package(pkg, scope="target", destination=target_folder)
        else:
            target_folder = host_folder
        copy(self, "LICENSE", host_folder, os.path.join(self.package_folder, "licenses"))
        host_folder = os.path.join(host_folder, "nvvm")
        target_folder = os.path.join(target_folder, "nvvm")
        copy(self, "*", os.path.join(target_folder, "bin"), os.path.join(self.package_folder, "bin"))
        if self.settings.os == "Linux":
            copy(self, "*.so*", os.path.join(target_folder, "lib64"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.lib", os.path.join(target_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", os.path.join(target_folder, "bin", "x64"), os.path.join(self.package_folder, "bin"))
        copy(self, "*", os.path.join(host_folder, "libdevice"), os.path.join(self.package_folder, "libdevice"))
        copy(self, "*", os.path.join(target_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "cicc*", os.path.join(host_folder, "bin"), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libs = ["nvvm"]
        self.cpp_info.resdirs = ["libdevice"]
        self.runenv_info.define_path("LIBNVVM_HOME", self.package_folder)
        self.runenv_info.define_path("CICC_PATH", os.path.join(self.package_folder, "bin"))
        self.runenv_info.define_path("NVVMIR_LIBRARY_DIR", os.path.join(self.package_folder, "libdevice"))
