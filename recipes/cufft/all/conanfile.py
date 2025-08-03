import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.18"


class CuFFTConan(ConanFile):
    name = "cufft"
    description = "cuFFT: CUDA Fast Fourier Transform library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cufft/"
    topics = ("cuda", "fft", "fftw", "fast-fourier-transform")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
        "nocallback": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
        "nocallback": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.use_stubs
            del self.options.nocallback
            self.package_type = "shared-library"

    def configure(self):
        if not self.options.get_safe("shared", True):
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def requirements(self):
        versions = self._utils.get_cuda_package_versions(self)
        self.requires(f"cudart/[~{versions['cuda_cudart']}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self._utils.validate_cuda_package(self, "libcufft")

    def build(self):
        self._utils.download_cuda_package(self, "libcufft")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            elif self.options.nocallback:
                copy(self, "libcufft_static_nocallback.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "libcufftw_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "none")

        if self.options.get_safe("shared", True):
            suffix = ""
        elif self.options.get_safe("nocallback", False):
            suffix = "_static_nocallback"
        else:
            suffix = "_static"

        v = self._cuda_version
        self.cpp_info.components["cufft_"].set_property("pkg_config_name", f"cufft-{v.major}.{v.minor}")
        self.cpp_info.components["cufft_"].set_property("component_version", f"{v.major}.{v.minor}")
        self.cpp_info.components["cufft_"].set_property("cmake_target_name", f"CUDA::cufft{suffix}")
        if self.options.get_safe("cmake_alias"):
            aliases = ["CUDA::cufft", "CUDA::cufft_static", "CUDA::cufft_static_nocallback"]
            aliases.remove(f"CUDA::cufft{suffix}")
            self.cpp_info.components["cufft_"].set_property("cmake_target_aliases", aliases)
        self.cpp_info.components["cufft_"].libs = [f"cufft{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cufft_"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["cufft_"].requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cufft_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.components["cufft_"].requires.append("cudart::culibos")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        self.cpp_info.components["cufftw"].set_property("pkg_config_name", f"cufftw-{v.major}.{v.minor}")
        self.cpp_info.components["cufftw"].set_property("component_version", f"{v.major}.{v.minor}")
        self.cpp_info.components["cufftw"].set_property("cmake_target_name", f"CUDA::cufftw{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias = "cufftw_static" if self.options.shared else "cufftw"
            self.cpp_info.components["cufftw"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cufftw"].libs = [f"cufftw{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cufftw"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["cufftw"].requires = ["cufft_"]
