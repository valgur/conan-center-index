import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class TensorRtConan(ConanFile):
    name = "tensorrt"
    description = "NVIDIA TensorRT is an SDK that facilitates high-performance machine learning inference."
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-TensorRT-License-Agreement"
    homepage = "https://developer.nvidia.com/tensorrt"
    topics = ("deep-learning", "neural-networks", "dnn", "gpu-acceleration", "inference", "nvidia", "cuda", "nvinfer")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "data": [True, False],
        "tools": [True, False],
        "samples": [True, False],
        "cmake_alias": [True, False],
        "nvinfer_builder_resource": [True, False],
        "nvinfer_builder_resource_win": [True, False],
    }
    default_options = {
        "shared": False,
        "data": False,
        "tools": True,
        "samples": False,
        "cmake_alias": True,
        "nvinfer_builder_resource": True,  # 1.3 GB runtime library - consider disabling
        "nvinfer_builder_resource_win": False,  # Windows builder resource library used for cross-platform support - 1.1 GB, skip by default
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.cmake_alias
            self.package_type = "shared-library"
        if Version(self.version) < "10.0" or self.settings.os != "Linux":
            del self.options.install_windows_builder

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        del self.info.settings.cuda.platform
        self.info.options.rm_safe("cmake_alias")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if Version(self.version) < "10.0":
            self.cuda.requires("cublas")
            self.requires("cudnn/[^8]")

        # TensorRT archives also used to provide libonnx_proto.a (merged into nvonnxparser since 10.13.2).
        # Get it from the onnx::onnx_proto component in the onnx package instead.

    @cached_property
    def _platform(self):
        return {
            ("Linux", "x86_64"): "linux-x86_64",
            ("Linux", "armv8"): "linux-aarch64",
            ("Windows", "x86_64"): "windows-x86_64",
        }.get((self.settings.os.value, self.settings.arch.value))

    @cached_property
    def _cuda_version(self):
        return int(Version(self.settings.cuda.version).major.value)

    def validate(self):
        if self._platform is None:
            raise ConanInvalidConfiguration(f"{self.settings.arch} {self.settings.os} is not supported")
        if self._cuda_version not in self.conan_data["sources"][self.version][self._platform]:
            raise ConanInvalidConfiguration(f"{self.ref} {self._platform} does not support CUDA {self._cuda_version}")
        if Version(self.version) < "10.0" and self.options.get_safe("shared", True):
            self.cuda.require_shared_deps(["cublas", "cudnn"])

    def build(self):
        get(self, **self.conan_data["sources"][self.version][self._platform][self._cuda_version],
            destination=self.source_folder, strip_root=True)

    def package(self):
        copy(self, "doc/Acknowledgements.txt", self.source_folder, os.path.join(self.package_folder, "licenses"), keep_path=False)

        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, f"lib*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"), excludes=["*builder*"])
            else:
                # Don't copy libonnx_proto.a
                copy(self, f"libnv*.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            rm(self, "libnvcaffe*", os.path.join(self.package_folder, "lib"))
            if self.options.nvinfer_builder_resource:
                copy(self, "libnvinfer_builder_resource.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            if self.options.get_safe("install_windows_builder", False):
                copy(self, "libnvinfer_builder_resource.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, f"*.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            copy(self, f"*.dll", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "bin"))

        if self.options.tools:
            copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

        if self.options.data:
            copy(self, "*", os.path.join(self.source_folder, "data"), os.path.join(self.package_folder, "share", "tensorrt", "data"))

        if self.options.samples:
            copy(self, "*", os.path.join(self.source_folder, "samples"), os.path.join(self.package_folder, "share", "tensorrt", "samples"))

    def package_info(self):
        # The TensorRT archives do not officially export any CMake config or .pc files.
        # The CMake names at least match the output of FindTensorRT.cmake in Holoscan SDK, though:
        # https://github.com/nvidia-holoscan/holoscan-sdk/blob/main/cmake/modules/FindTensorRT.cmake
        self.cpp_info.set_property("cmake_file_name", "TensorRT")

        suffix = "" if self.options.get_safe("shared", True) else "_static"
        alias_suffix = "_static" if self.options.get_safe("shared", True) else ""

        def add_component(name, requires=None):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", f"TensorRT::{name}{suffix}")
            if self.options.get_safe("cmake_alias"):
                component.set_property("cmake_target_aliases", [f"TensorRT::{name}{alias_suffix}"])
            win_suffix = f"_{Version(self.version).major}" if self.settings.os == "Windows" else ""
            component.libs = [f"{name}{suffix}{win_suffix}"]
            component.set_property("pkg_config_name", name)
            component.requires = requires or []
            component.requires.append("cudart::cudart_")
            if self.settings.os == "Linux":
                if not self.options.shared:
                    component.system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]

        add_component("nvinfer")
        add_component("nvinfer_lean")
        add_component("nvinfer_vc_plugin")

        if Version(self.version) >= "10.0":
            add_component("nvinfer_dispatch")
            add_component("nvinfer_plugin", requires=["nvinfer"])
            add_component("nvonnxparser")
        else:
            add_component("nvinfer_dispatch", requires=["nvinfer"])
            add_component("nvinfer_plugin", requires=["nvinfer", "cublas::cublas_", "cudnn::cudnn_shim"])
            add_component("nvonnxparser", requires=["nvinfer", "nvinfer_plugin"])
            add_component("nvparsers", requires=["nvinfer", "nvinfer_plugin"])
            # nvcaffe_parser is just a symlink to nvparsers in the archive
            self.cpp_info.components["nvcaffe_parser"].set_property("cmake_target_name", "TensorRT::nvcaffe_parser")
            self.cpp_info.components["nvcaffe_parser"].set_property("pkg_config_name", "nvcaffe_parser")
            self.cpp_info.components["nvcaffe_parser"].requires = ["nvparsers"]

        if self.options.data:
            self.cpp_info.components["nvinfer"].resdirs.append("share/tensorrt/data")
        if self.options.samples:
            self.cpp_info.components["nvinfer"].resdirs.append("share/tensorrt/samples")
