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
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/gpudirect-storage/api-reference-guide/"
    topics = ("cuda", "gpudirect", "rdma")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
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

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if self.options.cufile_rdma:
            self.requires("rdma-core/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("cuFile is only available on Linux")
        self.cuda.validate_package("libcufile")
        if self.options.shared:
            self.cuda.require_shared_deps(["rdma-core"])

    def build(self):
        self.cuda.download_package("libcufile")

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

        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""

        self.cpp_info.components["cufile_"].set_property("cmake_target_name", f"CUDA::cuFile{suffix}")
        if self.options.cmake_alias:
            self.cpp_info.components["cufile_"].set_property("cmake_target_aliases", [f"CUDA::cuFile{alias_suffix}"])
        self.cpp_info.components["cufile_"].set_property("pkg_config_name", f"cufile-{self.cuda.version}")
        self.cpp_info.components["cufile_"].set_property("component_version", str(self.cuda.version))
        self.cpp_info.components["cufile_"].libs = [f"cufile{suffix}"]
        if not self.options.shared:
            self.cpp_info.components["cufile_"].system_libs = ["rt", "pthread", "m", "gcc_s", "stdc++"]
        self.cpp_info.components["cufile_"].requires = ["cudart::cudart_"]

        if self.options.cufile_rdma:
            self.cpp_info.components["cufile_rdma"].set_property("cmake_target_name", f"CUDA::cuFile_rdma{suffix}")
            if self.options.cmake_alias:
                self.cpp_info.components["cufile_rdma"].set_property("cmake_target_aliases", [f"CUDA::cuFile_rdma{alias_suffix}"])
            self.cpp_info.components["cufile_rdma"].set_property("pkg_config_name", f"cufile_rdma-{self.cuda.version}")
            self.cpp_info.components["cufile_rdma"].set_property("component_version", str(self.cuda.version))
            self.cpp_info.components["cufile_rdma"].libs = [f"cufile_rdma{suffix}"]
            self.cpp_info.components["cufile_rdma"].requires = [
                "cufile_",
                "rdma-core::libmlx5",
                "rdma-core::librdmacm",
                "rdma-core::libibverbs",
            ]
