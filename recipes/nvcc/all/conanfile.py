import json
import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain
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

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @property
    def _cross_toolchain(self):
        return self.settings_target and self.settings.arch != self.settings_target.arch

    @staticmethod
    def _platform_id(settings):
        if settings.get_safe("cuda.platform") == "sbsa":
            if settings.os != "Linux" or settings.arch != "armv8":
                raise ConanInvalidConfiguration(f"Invalid OS/arch combination for cuda.platform=sbsa: {settings.os}/{settings.arch}")
            return "linux-sbsa"
        return {
            ("Windows", "x86_64"): "windows-x86_64",
            ("Linux", "x86_64"): "linux-x86_64",
            ("Linux", "armv8"): "linux-aarch64",
        }.get((str(settings.os), str(settings.arch)))

    @property
    def _host_platform_id(self):
        return self._platform_id(self.settings)

    @property
    def _target_platform_id(self):
        return self._platform_id(self.settings_target)

    def validate(self):
        if self._host_platform_id is None:
            raise ConanInvalidConfiguration(f"Unsupported platform: {self.settings.os}/{self.settings.arch}")
        if self._cross_toolchain:
            if self.settings.os != self.settings_target.os:
                raise ConanInvalidConfiguration("Host and target OS-s must match")
            if self._target_platform_id is None:
                raise ConanInvalidConfiguration(f"Unsupported cross-compilation arch: {self.settings.arch}")
        if not self.settings.get_safe("cuda.architectures"):
            raise ConanInvalidConfiguration("cuda.architectures setting must be defined")
        if not self._arch_flags:
            raise ConanInvalidConfiguration("No valid CUDA architectures found in cuda.architectures setting")

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

    @cached_property
    def _arch_flags(self):
        # https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/#gpu-name-gpuname-arch
        flags = []
        for arch in str(self.settings.cuda.architectures).split(","):
            if arch in ["native", "all", "all-major"]:
                flags.append(f"-arch={arch}")
                continue
            virtual = True
            real = True
            if "-" in arch:
                arch, suffix = arch.split("-", 1)
                if suffix == "virtual":
                    real = False
                elif suffix == "real":
                    virtual = False
                else:
                    raise ConanInvalidConfiguration(f"Unknown CUDA architecture suffix: {suffix}")
            if real:
                flags.append(f"-gencode=arch=compute_{arch},code=sm_{arch}")
            if virtual:
                flags.append(f"-gencode=arch=compute_{arch},code=compute_{arch}")
        return " ".join(flags)

    def package_info(self):
        cudaflags = self.conf.get("user.tools.build:cudaflags", "")
        cudaflags += f" --cudart={self.settings.cuda.runtime}"
        cudaflags += f" {self._arch_flags}"
        cudaflags = cudaflags.strip()

        cc = AutotoolsToolchain(self).vars().get("CC", None)
        if not self._cross_toolchain and cc:
            self.runenv_info.define_path("CUDAHOSTCXX", cc)
        # Conan currently does not provide a way to get the target compiler executable
        # cudaflags += f' -ccbin "{cc}'

        self.runenv_info.define("CUDAFLAGS", cudaflags)
        self.conf_info.define("user.nvcc:arch_flags", self._arch_flags)

        ext = ".exe" if self.settings.os == "Windows" else ""
        nvcc = os.path.join(self.package_folder, "bin", "nvcc" + ext)
        self.conf_info.update("tools.build:compiler_executables", {"cuda": nvcc})
        self.runenv_info.define_path("CUDACXX", nvcc + " " + cudaflags)
