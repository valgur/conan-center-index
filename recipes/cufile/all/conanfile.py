import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.18"


class CuFileConan(ConanFile):
    name = "cufile"
    description = "NVIDIA GPUDirect Storage cuFile library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement"
    homepage = "https://docs.nvidia.com/gpudirect-storage/api-reference-guide/"
    topics = ("cuda", "gpudirect", "rdma")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "cufile_rdma": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "cufile_rdma": False,
        "tools": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @cached_property
    def _cuda_version(self):
        url = self.conan_data["sources"][self.version]["url"]
        return Version(url.rsplit("_")[1].replace(".json", ""))

    def requirements(self):
        versions = self._utils.get_cuda_package_versions(self)
        self.requires(f"cudart/[~{versions['cuda_cudart']}]", transitive_headers=True, transitive_libs=True)
        if self.options.cufile_rdma:
            self.requires("rdma-core/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuFile is only available on Linux")
        self._utils.validate_cuda_package(self, "libcufile")

    def build(self):
        self._utils.download_cuda_package(self, "libcufile")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "etc"), os.path.join(self.package_folder, "etc"))
        if self.options.tools:
            copy(self, "*", os.path.join(self.source_folder, "tools"), os.path.join(self.package_folder, "bin"))
        if self.options.shared:
            copy(self, "libcufile.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.cufile_rdma:
                copy(self, "libcufile_rdma.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "libcufile_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.cufile_rdma:
                copy(self, "libcufile_rdma_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))


    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "none")

        v = self._cuda_version
        self.cpp_info.components["cufile_"].set_property("pkg_config_name", f"cufile-{v.major}.{v.minor}")
        self.cpp_info.components["cufile_"].set_property("component_version", f"{v.major}.{v.minor}")
        lib = "cufile" if self.options.shared else "cufile_static"
        self.cpp_info.components["cufile_"].set_property("cmake_target_name", f"CUDA::{lib}")
        if self.options.cmake_alias:
            alias = "cufile_static" if self.options.shared else "cufile"
            self.cpp_info.components["cufile_"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
        self.cpp_info.components["cufile_"].libs = [lib]
        if not self.options.shared:
            self.cpp_info.components["cufile_"].system_libs = ["rt", "pthread", "m", "gcc_s", "stdc++"]
        self.cpp_info.components["cufile_"].requires = ["cudart::cudart_"]

        if self.options.cufile_rdma:
            self.cpp_info.components["cufile_rdma"].set_property("pkg_config_name", f"cufile_rdma-{v.major}.{v.minor}")
            self.cpp_info.components["cufile_rdma"].set_property("component_version", f"{v.major}.{v.minor}")
            lib = "cufile_rdma" if self.options.shared else "cufile_rdma_static"
            self.cpp_info.components["cufile_rdma"].set_property("cmake_target_name", f"CUDA::{lib}")
            if self.options.cmake_alias:
                alias = "cufile_rdma_static" if self.options.shared else "cufile_rdma"
                self.cpp_info.components["cufile_rdma"].set_property("cmake_target_aliases", [f"CUDA::{alias}"])
            self.cpp_info.components["cufile_rdma"].libs = [lib]
            self.cpp_info.components["cufile_rdma"].requires = [
                "cufile_",
                "rdma-core::libmlx5",
                "rdma-core::librdmacm",
                "rdma-core::libibverbs",
            ]
