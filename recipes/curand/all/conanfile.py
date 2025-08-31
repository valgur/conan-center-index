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

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

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
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        if not self.options.shared:
            self.requires(f"culibos/[~{self.settings.cuda.version}]")

    def validate(self):
        self._utils.validate_cuda_package(self, "libcurand")
        if Version(self.settings.cuda.version).major == 11 and Version(self.version) >= "10.4":
            raise ConanInvalidConfiguration("CUDA 11 is only compatible with cuRAND 10.3 or lower")

    def build(self):
        self._utils.download_cuda_package(self, "libcurand")

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
            copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        v = self._cuda_version
        self.cpp_info.set_property("pkg_config_name", f"curand-{v.major}.{v.minor}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::curand{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias = "curand_static" if self.options.shared else "curand"
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.libs = [f"curand{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.libdirs = ["lib/stubs", "lib"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.requires.append("culibos::culibos")
