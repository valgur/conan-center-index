import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvCompConan(ConanFile):
    name = "nvcomp"
    description = "The nvCOMP library provides fast lossless data compression and decompression using a GPU"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://developer.nvidia.com/nvcomp/"
    topics = ("cuda", "compression", "snappy", "zstd", "deflate", "lz4")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.cuda_version = self.info.settings.cuda.version
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self.cuda.validate_package("nvcomp")
        if self.settings.os == "Windows" and not is_msvc(self):
            raise ConanInvalidConfiguration("nvcomp only supports MSVC on Windows")

    def build(self):
        self.cuda.download_package("nvcomp")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "NOTICE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib")
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", libdir, os.path.join(self.package_folder, "lib"))
                copy(self, "libnvcomp_device_static.a", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", libdir, os.path.join(self.package_folder, "lib"))
        else:
            if self.options.shared:
                copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
                copy(self, "*.lib", libdir, os.path.join(self.package_folder, "lib"), excludes="*_static.lib")
                copy(self, "nvcomp_device_static.lib", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.lib", libdir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""
        self.cpp_info.set_property("cmake_file_name", "nvcomp")
        self.cpp_info.components["nvcomp_"].set_property("cmake_target_name", f"nvcomp::nvcomp{suffix}")
        aliases = [f"CUDA::nvcomp{suffix}"]
        if self.options.get_safe("cmake_alias"):
            aliases.extend([f"nvcomp::nvcomp{alias_suffix}", f"CUDA::nvcomp{alias_suffix}"])
        self.cpp_info.components["nvcomp_"].set_property("cmake_target_aliases", aliases)
        self.cpp_info.components["nvcomp_"].libs = [f"nvcomp{suffix}"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["nvcomp_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
        self.cpp_info.components["nvcomp_"].requires = ["cudart::cudart_"]
        if not self.options.shared:
            self.cpp_info.components["nvcomp_"].defines.append("NVCOMP_STATIC_DEFINE")

        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""
        self.cpp_info.components["nvcomp_cpu"].set_property("cmake_target_name", f"nvcomp::nvcomp_cpu{suffix}")
        aliases = [f"CUDA::nvcomp_cpu{suffix}"]
        if self.options.get_safe("cmake_alias"):
            aliases.extend([f"nvcomp::nvcomp_cpu{alias_suffix}", f"CUDA::nvcomp_cpu{alias_suffix}"])
        self.cpp_info.components["nvcomp_cpu"].set_property("cmake_target_aliases", aliases)
        self.cpp_info.components["nvcomp_cpu"].libs = [f"nvcomp_cpu{suffix}"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["nvcomp_cpu"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
        if not self.options.shared:
            self.cpp_info.components["nvcomp_cpu"].defines.append("NVCOMP_STATIC_DEFINE")

        if Version(self.version) < "5.0":
            self.cpp_info.components["nvcomp_device"].set_property("cmake_target_name", "nvcomp::nvcomp_device_static")
            aliases = ["CUDA::nvcomp_device_static"]
            if self.options.get_safe("cmake_alias"):
                aliases.extend(["nvcomp::nvcomp_device", "CUDA::nvcomp_device"])
            self.cpp_info.components["nvcomp_device"].set_property("cmake_target_aliases", aliases)
            self.cpp_info.components["nvcomp_device"].libs = ["nvcomp_device_static"]
            self.cpp_info.components["nvcomp_device"].includedirs = ["include/nvcomp/device"]
            if self.settings.os == "Linux":
                self.cpp_info.components["nvcomp_device"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.components["nvcomp_device"].requires = ["nvcomp_", "cudart::cudart_"]
