import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvJpeg2kConan(ConanFile):
    name = "nvjpeg2k"
    description = "The nvJPEG2000 library accelerates the decoding and encoding of JPEG2000 images on NVIDIA GPUs"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/nvjpeg2000/"
    topics = ("cuda", "jpeg2k", "codec")
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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)

    def validate(self):
        self.cuda.validate_package("libnvjpeg_2k")
        if self.cuda.major >= 13 and Version(self.version) < "0.9":
            raise ConanInvalidConfiguration(f"CUDA {self.settings.cuda.version} requires nvjpeg2k >= 0.9")

    def build(self):
        self.cuda.download_package("libnvjpeg_2k")
        if self.version == "0.9.0.43":
            # Fix 'error: unknown type name ‘nvjpeg2kQualityType’; did you mean ‘nvjpeg2kQualityType_t’?'
            replace_in_file(self, os.path.join(self.source_folder, "include/nvjpeg2k.h"),
                            "nvjpeg2kQualityType quality_type",
                            "nvjpeg2kQualityType_t quality_type")
            # Fix 'error: unknown type name ‘nvjpeg2kProgOrder’'
            replace_in_file(self, os.path.join(self.source_folder, "include/nvjpeg2k.h"),
                            "nvjpeg2kProgOrder prog_order",
                            "nvjpeg2kProgOrder_t prog_order")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib", str(self.cuda.version.major))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*_static.a", libdir, os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dll", libdir, os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", libdir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        # Neither the CMake nor .pc name is official
        self.cpp_info.set_property("pkg_config_name", f"nvjpeg2k-{self.cuda.version}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::nvjpeg2k{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::nvjpeg2k{alias_suffix}"])
        self.cpp_info.libs = [f"nvjpeg2k{suffix}"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
