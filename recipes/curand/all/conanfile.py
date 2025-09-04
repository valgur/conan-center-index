import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuRandConan(ConanFile):
    name = "curand"
    description = "cuRAND: CUDA random number generation library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/curand/"
    topics = ("cuda", "random", "rng")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.use_stubs
            self.package_type = "shared-library"

    def configure(self):
        if not self.options.get_safe("shared", True):
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if self.settings.os == "Linux" and not self.options.shared:
            self.cuda.requires("culibos")

    def validate(self):
        self.cuda.validate_package("libcurand")
        if self.cuda.version.major == 11 and Version(self.version) >= "10.4":
            raise ConanInvalidConfiguration("CUDA 11 is only compatible with cuRAND 10.3 or lower")

    def build(self):
        self.cuda.download_package("libcurand")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            lib_dir = os.path.join(self.source_folder, "lib", "x64")
            bin_dir = os.path.join(self.source_folder, "bin", "x64") if self.cuda.major >= 13 else os.path.join(self.source_folder, "bin")
            copy(self, "*.lib", lib_dir, os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", bin_dir, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
        self.cpp_info.set_property("pkg_config_name", f"curand-{self.cuda.version}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::curand{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::curand{alias_suffix}"])
        self.cpp_info.libs = [f"curand{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.libdirs = ["lib/stubs", "lib"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.requires.append("culibos::culibos")
