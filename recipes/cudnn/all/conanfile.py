import os

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
        "legacy_api": [True, False],
        "precompiled": [True, False],
        "cmake_alias": [True, False],
    }
    default_options = {
        "shared": False,
        "legacy_api": False,
        "precompiled": False,
        "cmake_alias": True,
    }
    options_description = {
        "legacy_api": "Install the cuDNN Legacy API libraries in addition to the Graph API.",
        "precompiled": (
            "If False, rely on JIT compilation of the kernels instead of installing precompiled ones. "
            "The precompiled libraries are significantly larger at 800 MB vs 25 MB for the JIT version."
        ),
        "cmake_alias": "Always create both shared and static CMake targets regardless of shared=True/False.",
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"
        if Version(self.version) < "9.10":
            del self.options.precompiled

    def configure(self):
        if self.options.legacy_api:
            self.options.rm_safe("precompiled")
        if not self.options.get_safe("precompiled", True):
            self.options.rm_safe("shared")
            self.package_type = "shared-library"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
        self._utils.cuda_requires(self, "cublas")
        self._utils.cuda_requires(self, "nvrtc")
        self._utils.cuda_requires(self, "nvptxcompiler")
        if self.settings.os == "Linux":
            self.requires("zlib-ng/[^2.0]")

    def validate(self):
        pkg = "cudnn" if self.options.get_safe("precompiled", True) else "cudnn_jit"
        self._utils.validate_cuda_package(self, pkg)
        if self.options.legacy_api and not self.options.get_safe("precompiled", True):
            raise ConanInvalidConfiguration("legacy_api=True requires precompiled=True")

    def build(self):
        pkg = "cudnn" if self.options.get_safe("precompiled", True) else "cudnn_jit"
        self._utils.download_cuda_package(self, pkg)

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
        copy_lib("cudnn_graph")
        copy_lib("cudnn_engines_runtime_compiled")

        if self.options.get_safe("precompiled", True):
            copy_lib("cudnn_heuristic")
            copy_lib("cudnn_engines_precompiled")

        if self.options.legacy_api:
            copy_lib("cudnn_adv")
            copy_lib("cudnn_cnn")
            copy_lib("cudnn_ops")

    def package_info(self):
        # https://docs.nvidia.com/deeplearning/cudnn/installation/latest/build-run-cudnn.html
        # https://docs.nvidia.com/deeplearning/cudnn/backend/latest/api/overview.html

        # The CMake file and target names are not official, nor are the pkg-config names.
        self.cpp_info.set_property("cmake_file_name", "cuDNN")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""

        def add_component(name, requires=None):
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

        # cudnn shim library - prefer cudnn_graph instead for non-legacy applications
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
            self.cpp_info.components["cudnn_shim"].requires = ["cudnn_graph"]
            if self.options.legacy_api:
                self.cpp_info.components["cudnn_shim"].requires.extend(["cudnn_adv", "cudnn_cnn", "cudnn_ops"])

        ext_requires = [
            "cublas::cublasLt",
            "nvrtc::nvrtc_",
            "nvptxcompiler::nvptxcompiler",
            "cudart::cudart_",
        ]
        if self.options.get_safe("shared", True):
            self.cpp_info.components["cudnn_shim"].requires.extend(ext_requires)

        add_component("cudnn_graph", requires=ext_requires)
        if self.options.legacy_api:
            add_component("cudnn_adv", requires=["cudnn_ops"])
            add_component("cudnn_cnn", requires=["cudnn_ops"])
            add_component("cudnn_ops", requires=["cudnn_graph"])

        # These should only be used for static linking.
        # They are loaded dynamically at runtime by cudnn_graph when shared=True.
        if not self.options.get_safe("shared", True):
            add_component("cudnn_heuristic")
            add_component("cudnn_engines_runtime_compiled", requires=["cudnn_heuristic", "nvrtc::nvrtc_"])
            add_component("cudnn_engines_precompiled", requires=["cudnn_heuristic", "nvrtc::nvrtc_"])
            self.cpp_info.components["cudnn_graph"].requires.extend(["cudnn_engines_runtime_compiled", "cudnn_engines_precompiled"])

            # A dirty hack to resolve circular dependencies on Linux
            if self.settings.os == "Linux":
                self.cpp_info.components["cudnn_graph"].sharedlinkflags = ["-Wl,--start-group"]
                self.cpp_info.components["cudnn_graph"].exelinkflags = ["-Wl,--start-group"]
                self.cpp_info.components["cudnn_heuristic"].system_libs.append("-Wl,--end-group")
