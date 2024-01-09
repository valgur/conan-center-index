import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get, move_folder_contents
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class LibcudacxxConan(ConanFile):
    name = "libcudacxx"
    description = ("libcu++, the NVIDIA C++ Standard Library, is the C++ Standard Library for your entire system."
                   " It provides a heterogeneous implementation of the C++ Standard Library that can be used in and between CPU and GPU code.")
    license = "BSD 3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://nvidia.github.io/libcudacxx/"
    topics = ("standard-library", "libcxx", "cuda", "gpu", "nvidia", "nvidia-hpc-sdk", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _min_cppstd(self):
        return 11

    @property
    def _compilers_minimum_version(self):
        # https://nvidia.github.io/libcudacxx/setup/requirements.html#nvcc-host-compilers
        return {
            "Visual Studio": "15",
            "msvc": "191",
            "gcc": "5",
            "clang": "7",
            "apple-clang": "10",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        move_folder_contents(self, os.path.join(self.source_folder, "libcudacxx"), self.source_folder)

    def package(self):
        copy(self, "LICENSE.TXT",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*",
             src=os.path.join(self.source_folder, "include"),
             dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []

        # Follows the naming conventions of the official CMake config file:
        # https://github.com/NVIDIA/cccl/blob/main/libcudacxx/lib/cmake/libcudacxx/libcudacxx-config.cmake
        self.cpp_info.set_property("cmake_file_name", "libcudacxx")
        self.cpp_info.set_property("cmake_target_name", "libcudacxx::libcudacxx")

        # FIXME: CMakeDeps exports libcudacxx as a SYSTEM include, which will cause issues with nvcc
        # https://github.com/NVIDIA/cccl/blob/v2.2.0/libcudacxx/lib/cmake/libcudacxx/libcudacxx-config.cmake#L11-L29
