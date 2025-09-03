import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.18"


class CuFFTConan(ConanFile):
    name = "cufft"
    description = "cuFFT: CUDA Fast Fourier Transform library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cufft/"
    topics = ("cuda", "fft", "fftw", "fast-fourier-transform")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
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
        "nocallback": False,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.use_stubs
            del self.options.nocallback
            self.package_type = "shared-library"
        if Version(self.version) >= "12.0":
            self.options.rm_safe("nocallback")

    def configure(self):
        if self.options.get_safe("shared", True):
            self.options.rm_safe("nocallback")
        else:
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if self.settings.os == "Linux" and not self.options.shared:
            self.cuda.requires("culibos")

    def validate(self):
        self.cuda.validate_package("libcufft")
        package_cuda_major = Version(self.conan_data["sources"][self.version]["url"].rsplit("_")[1].replace(".json", "")).major
        if package_cuda_major != self.cuda.major:
            raise ConanInvalidConfiguration(f"{self.ref} expects CUDA v{self.cuda.version.major}, but cuda.version={self.settings.cuda.version}")

    def build(self):
        self.cuda.download_package("libcufft")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            elif self.options.get_safe("nocallback"):
                copy(self, "libcufft_static_nocallback.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "libcufftw_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            bin_dir = os.path.join(self.source_folder, "bin", "x64") if Version(self.version) >= 12 else os.path.join(self.source_folder, "bin")
            lib_dir = os.path.join(self.source_folder, "lib", "x64")
            copy(self, "*.dll", bin_dir, os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", lib_dir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "none")

        if self.options.get_safe("shared", True):
            suffix = ""
        elif self.options.get_safe("nocallback", False):
            suffix = "_static_nocallback"
        else:
            suffix = "_static"

        self.cpp_info.components["cufft_"].set_property("pkg_config_name", f"cufft-{self.cuda.version}")
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
            self.cpp_info.components["cufft_"].requires.append("culibos::culibos")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        self.cpp_info.components["cufftw"].set_property("pkg_config_name", f"cufftw-{self.cuda.version}")
        self.cpp_info.components["cufftw"].set_property("cmake_target_name", f"CUDA::cufftw{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias = "cufftw_static" if self.options.get_safe("shared", True) else "cufftw"
            self.cpp_info.components["cufftw"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cufftw"].libs = [f"cufftw{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cufftw"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["cufftw"].requires = ["cufft_"]
