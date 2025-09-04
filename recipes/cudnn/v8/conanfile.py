import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuDnnConan(ConanFile):
    name = "cudnn"
    description = "cuDNN: NVIDIA CUDA Deep Neural Network is a GPU-accelerated library of primitives for deep neural networks"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://developer.nvidia.com/cudnn"
    topics = ("cuda", "deep-learning", "neural-networks", "dnn", "gpu-acceleration")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "train": [True, False],
        "infer": [True, False],
        "cmake_alias": [True, False],
    }
    default_options = {
        "shared": False,
        "train": False,
        "infer": True,
        "cmake_alias": True,
    }
    options_description = {
        "train": "Install the cuDNN training API libraries.",
        "infer": "Install the cuDNN inference API libraries.",
        "cmake_alias": "Always create both shared and static CMake targets regardless of shared=True/False.",
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
        self.cuda.requires("cublas")
        self.cuda.requires("nvrtc")
        self.cuda.requires("nvptxcompiler")
        if self.settings.os == "Linux":
            self.requires("zlib-ng/[^2.0]")
            if not self.options.shared:
                self.cuda.requires("culibos")

    def validate(self):
        self.cuda.validate_package("cudnn")
        if not self.options.train and not self.options.infer:
            raise ConanInvalidConfiguration("At least one of 'train' or 'infer' options must be enabled.")

    def build(self):
        self.cuda.download_package("cudnn")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

        def copy_lib(name):
            major = Version(self.version).major
            if self.settings.os == "Linux":
                if self.options.get_safe("shared", True):
                    copy(self, f"lib{name}.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"lib{name}_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                    copy(self, f"lib{name}_static_v{major}.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, f"{name}.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
                copy(self, f"{name}64_{major}.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
                copy(self, f"{name}64_{major}.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

        copy_lib("cudnn")
        for lib in ["cudnn_adv", "cudnn_cnn", "cudnn_ops"]:
            if self.options.train:
                copy_lib(f"{lib}_train")
            if self.options.infer:
                copy_lib(f"{lib}_infer")

    def package_info(self):
        # https://docs.nvidia.com/deeplearning/cudnn/archives/cudnn-897/install-guide/index.html#add-lib-dep-pro

        # The CMake file and target names are not official, nor are the pkg-config names.
        self.cpp_info.set_property("cmake_file_name", "cuDNN")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""

        def add_component(base_name, requires=None):
            combined = self.cpp_info.components[base_name]
            combined.set_property("cmake_target_name", f"cuDNN::{base_name}{suffix}")
            if self.options.get_safe("cmake_alias"):
                combined.set_property("cmake_target_aliases", [f"cuDNN::{base_name}{alias_suffix}"])
            combined.set_property("pkg_config_name", base_name)
            names = []
            if self.options.train:
                names.append(f"{base_name}_train")
            if self.options.infer:
                names.append(f"{base_name}_infer")
            for name in names:
                component = self.cpp_info.components[name]
                component.set_property("cmake_target_name", f"cuDNN::{name}{suffix}")
                if self.options.get_safe("cmake_alias"):
                    component.set_property("cmake_target_aliases", [f"cuDNN::{name}{alias_suffix}"])
                component.set_property("pkg_config_name", name)
                component.libs = [f"{name}{suffix}"]
                component.requires = requires or []
                if self.settings.os == "Linux":
                    component.requires.append("zlib-ng::zlib-ng")
                    if not self.options.get_safe("shared", True):
                        component.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
                combined.requires.append(name)

        # cudnn shim library
        self.cpp_info.components["cudnn_shim"].set_property("pkg_config_name", "cudnn")
        self.cpp_info.components["cudnn_shim"].set_property("cmake_target_name", f"cuDNN::cudnn{suffix}")
        self.cpp_info.set_property("pkg_config_name", "cuDNN")
        # For compatibility with PyTorch and Vcpkg
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["CUDNN"])
        aliases = ["cuDNN::cuDNN"]
        if self.options.get_safe("cmake_alias"):
            aliases.append(f"cuDNN::cudnn{alias_suffix}")
        self.cpp_info.components["cudnn_shim"].set_property("cmake_target_aliases", aliases)
        if self.options.get_safe("shared", True):
            self.cpp_info.components["cudnn_shim"].libs = ["cudnn"]
        else:
            self.cpp_info.components["cudnn_shim"].requires.extend(["cudnn_adv", "cudnn_cnn", "cudnn_ops"])

        ext_requires = [
            "cublas::cublas_",
            "cublas::cublasLt",
            "nvrtc::nvrtc_",
            "nvptxcompiler::nvptxcompiler",
            "cudart::cudart_",
        ]
        if self.settings.os == "Linux" and not self.options.shared:
            ext_requires.append("culibos::culibos")
        if self.options.get_safe("shared", True):
            self.cpp_info.components["cudnn_shim"].requires.extend(ext_requires)

        add_component("cudnn_adv", requires=["cudnn_ops"])
        add_component("cudnn_cnn", requires=["cudnn_ops"])
        add_component("cudnn_ops", requires=ext_requires)
