import json
import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudartConan(ConanFile):
    name = "cudart"
    description = "CUDA Runtime architecture dependent libraries"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "runtime")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    def config_options(self):
        if self.settings.cuda.runtime == "shared":
            self.package_type = "shared-library"
        else:
            self.package_type = "static-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def requirements(self):
        v = Version(self.version)
        self.requires(f"nvcc-headers/[~{v.major}.{v.minor}]", transitive_headers=True)
        self.requires(f"cuda-driver-stubs/[~{v.major}.{v.minor}]", transitive_headers=True, transitive_libs=True)

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
        package_name = "cuda_cudart"
        download(self, **self.conan_data["sources"][self.version], filename=os.path.join(self.build_folder, "redistrib.json"))
        redist_info = json.loads(load(self, "redistrib.json"))[package_name]
        assert redist_info["version"] == self.version
        return redist_info

    def package(self):
        package_info = self._redist_info[self._platform_id]
        url = "https://developer.download.nvidia.com/compute/cuda/redist/" + package_info["relative_path"]
        get(self, url, sha256=package_info["sha256"], strip_root=True, destination=self.build_folder)
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"))
        if self.settings.os == "Windows":
            copy(self, "*.lib", os.path.join(self.build_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            rm(self, "cuda.lib", os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*", os.path.join(self.build_folder, "lib"), os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "lib", "stubs"))
        if self.settings.cuda.runtime == "shared":
            rm(self, "*cudart_static.*", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*cudart.*", os.path.join(self.package_folder, "lib"))
            rm(self, "*cudart.*", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        # TODO: create a complete wrapper for CUDAToolkit.cmake
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "CUDAToolkit")

        lib = "cudart" if self.settings.cuda.runtime == "shared" else "cudart_static"
        self.cpp_info.components["cudart"].set_property("cmake_target_name", f"CUDA::{lib}")
        v = Version(self.version)
        self.cpp_info.components["cudart"].set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        self.cpp_info.components["cudart"].set_property("component_version", f"{v.major}.{v.minor}")
        alias = "cudart_static" if self.settings.cuda.runtime == "shared" else "cudart"
        self.cpp_info.components["cudart"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cudart"].libs = [lib]
        if self.settings.os == "Linux":
            self.cpp_info.components["cudart"].bindirs = []
            self.cpp_info.components["cudart"].system_libs = ["rt", "pthread", "dl"]
        self.cpp_info.components["cudart"].requires = ["nvcc-headers::nvcc-headers", "cuda-driver-stubs::cuda-driver-stubs"]

        self.cpp_info.components["cudadevrt"].set_property("cmake_target_name", "CUDA::cudadevrt")
        self.cpp_info.components["cudadevrt"].libs = ["cudadevrt"]
        self.cpp_info.components["cudadevrt"].requires = ["nvcc-headers::nvcc-headers", "cuda-driver-stubs::cuda-driver-stubs"]

        if self.settings.os == "Linux":
            self.cpp_info.components["culibos"].set_property("cmake_target_name", "CUDA::culibos")
            self.cpp_info.components["culibos"].libs = ["culibos"]
            self.cpp_info.components["culibos"].requires = ["nvcc-headers::nvcc-headers", "cuda-driver-stubs::cuda-driver-stubs"]
