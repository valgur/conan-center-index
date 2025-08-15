import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudaDriverStubsConan(ConanFile):
    name = "cuda-driver-stubs"
    description = "Stubs for the CUDA Driver library (libcuda.so)"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-End-User-License-Agreement AND MIT"  # MIT is for the vendored FindCUDA.cmake
    homepage = "https://developer.nvidia.com/cuda-toolkit"
    topics = ("cuda", "driver")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        copy(self, "CUDAToolkit-wrapper.cmake", self.recipe_folder, self.export_sources_folder)
        copy(self, "CUDA-wrapper.cmake", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures

    def validate(self):
        self._utils.validate_cuda_package(self, "cuda_cudart")

    def build(self):
        self._utils.download_cuda_package(self, "cuda_cudart")

    def _write_cuda_version(self):
        file = os.path.join(self.package_folder, "share", "conan", "CUDA-wrapper.cmake")
        content = load(self, file)
        v = Version(self.version)
        content = content.replace("@CUDA_VERSION@", f"{v.major}.{v.minor}")
        content = content.replace("@CUDA_VERSION_MAJOR@", str(v.major))
        content = content.replace("@CUDA_VERSION_MINOR@", str(v.minor))
        save(self, file, content)

    def _write_findcuda_license(self):
        content = load(self, os.path.join(self.package_folder, "share", "conan", "CUDA-wrapper.cmake"))
        license_text = content.split("###", 1)[0].replace("# ", "").replace("#", "")
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE.FindCUDA.cmake.txt"), license_text)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "cuda.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            copy(self, "libcuda.so", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "cuda.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

        cmake_dir = os.path.join(self.package_folder, "share", "conan")
        copy(self, "CUDAToolkit-wrapper.cmake", self.export_sources_folder, cmake_dir)
        copy(self, "CUDA-wrapper.cmake", self.export_sources_folder, cmake_dir)
        self._write_cuda_version()
        self._write_findcuda_license()
        base_url = "https://raw.githubusercontent.com/Kitware/CMake/refs/tags/v4.1.0/Modules/FindCUDA/"
        for filename, sha256 in [
            ("make2cmake.cmake", "fca2d9c4bdc08597a164ab9b4e1cb8a360bf8041f99a6e21de4329c4b1e06a35"),
            ("parse_cubin.cmake", "87729af1cfa6984d8c6a3974b3cdf8d9f6995953c06836ced6b33fe26fbe6330"),
            ("run_nvcc.cmake", "08b481160e506e2ad30825d505f611c4091ddf8941b7d4dc1bfaa59b70e97800"),
        ]:
            download(self, url=base_url + filename, sha256=sha256, filename=os.path.join(cmake_dir, filename))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "CUDA::cuda_driver")
        v = Version(self.version)
        self.cpp_info.set_property("pkg_config_name", f"cudart-{v.major}.{v.minor}")
        self.cpp_info.libs = ["cuda"]

        # Also install the wrapper for FindCUDAToolkit.cmake as cuda-driver-stubs is the root dependency for all other CUDA toolkit packages
        self.cpp_info.set_property("cmake_find_mode", "both")
        # A hacky way to support both FindCUDAToolkit.cmake and FindCUDA.cmake
        self.cpp_info.set_property("cmake_file_name", "CUDAToolkit")
        self.cpp_info.set_property("cmake_module_file_name", "CUDA")
        self.cpp_info.set_property("cmake_build_modules", [
            "share/conan/CUDAToolkit-wrapper.cmake",
            "share/conan/CUDA-wrapper.cmake",
        ])
        self.cpp_info.builddirs = ["share/conan"]
