import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NanoarrowConan(ConanFile):
    name = "nanoarrow"
    description = "Helpers for Arrow C Data & Arrow C Stream interfaces"
    license = "Apache-2.0"
    homepage = "https://github.com/apache/arrow-nanoarrow"
    topics = ("arrow", "data", "serialization", "ipc")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "ipc": [True, False],
        "with_zstd": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "ipc": False,
        "with_zstd": False,
        "with_cuda": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.ipc:
            self.options.with_zstd.value = False
        if not self.options.with_cuda:
            del self.settings.cuda
            self.languages = ["C"]

    def requirements(self):
        if self.options.ipc:
            self.requires("flatcc/[*]")
            if self.options.with_zstd:
                self.requires("zstd/[^1.5]")
        if self.options.with_cuda:
            self.requires(f"cuda-driver-stubs/[~{self.settings.cuda.version}]")

    def validate(self):
        if self.options.with_cuda:
            check_min_cppstd(self, 17)

    def build_requirements(self):
        if self.options.ipc:
            self.tool_requires("flatcc/[*]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "if(NOT NANOARROW_FLATCC_INCLUDE_DIR AND NOT NANOARROW_FLATCC_ROOT_DIR)",
                        "if(1)\nfind_package(flatcc REQUIRED)\nelseif(0)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["NANOARROW_IPC"] = self.options.ipc
        tc.cache_variables["NANOARROW_IPC_WITH_ZSTD"] = self.options.with_zstd
        tc.cache_variables["NANOARROW_DEVICE"] = self.options.with_cuda
        tc.cache_variables["NANOARROW_DEVICE_WITH_CUDA"] = self.options.with_cuda
        tc.cache_variables["NANOARROW_DEVICE_WITH_METAL"] = False  # TODO
        tc.cache_variables["NANOARROW_INSTALL_SHARED"] = self.options.shared
        if self.options.ipc:
            tc.cache_variables["NANOARROW_FLATCC_ROOT_DIR"] = self.dependencies["flatcc"].package_folder.replace("\\", "/")
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("zstd", "cmake_target_name", "zstd::libzstd")
        deps.set_property("flatcc", "cmake_target_name", "flatccrt")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "NOTICE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if self.options.shared:
            rm(self, "*_static.*", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nanoarrow")

        suffix = "_shared" if self.options.shared else "_static"

        self.cpp_info.components["nanoarrow_"].set_property("cmake_target_name", "nanoarrow::nanoarrow")
        self.cpp_info.components["nanoarrow_"].set_property("cmake_target_aliases", ["nanoarrow::nanoarrow_static", "nanoarrow::nanoarrow_shared"])
        self.cpp_info.components["nanoarrow_"].libs = ["nanoarrow" + suffix]
        if self.options.shared:
            self.cpp_info.components["nanoarrow_"].defines.append("NANOARROW_BUILD_DLL")
        if self.settings.build_type == "Debug":
            self.cpp_info.components["nanoarrow_"].defines.append("NANOARROW_DEBUG")

        if self.options.ipc:
            self.cpp_info.components["nanoarrow_ipc"].set_property("cmake_target_name", "nanoarrow::nanoarrow_ipc")
            self.cpp_info.components["nanoarrow_ipc"].set_property("cmake_target_aliases", ["nanoarrow::nanoarrow_ipc_static", "nanoarrow::nanoarrow_ipc_shared"])
            self.cpp_info.components["nanoarrow_ipc"].libs = ["nanoarrow_ipc" + suffix]
            self.cpp_info.components["nanoarrow_ipc"].requires = ["nanoarrow_", "flatcc::flatcc"]
            if self.options.with_zstd:
                self.cpp_info.components["nanoarrow_ipc"].requires.append("zstd::zstd")

        if self.options.with_cuda:
            self.cpp_info.components["nanoarrow_device"].set_property("cmake_target_name", "nanoarrow::nanoarrow_device")
            self.cpp_info.components["nanoarrow_device"].set_property("cmake_target_aliases", ["nanoarrow::nanoarrow_device_static", "nanoarrow::nanoarrow_device_shared"])
            self.cpp_info.components["nanoarrow_device"].libs = ["nanoarrow_device" + suffix]
            self.cpp_info.components["nanoarrow_device"].requires = ["nanoarrow_", "cuda-driver-stubs::cuda-driver-stubs"]
