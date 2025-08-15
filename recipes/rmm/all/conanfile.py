import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RmmConan(ConanFile):
    name = "rmm"
    description = "RAPIDS Memory Manager"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/rmm"
    topics = ("cuda", "memory-management", "memory-allocation", "rapids", "header-only")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rapids_logger/[>=0.1 <1]", transitive_headers=True, transitive_libs=True)
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        self.requires("nvtx/[^3]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)
        self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["rmm"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["rapids-cmake"], strip_root=True, destination="cpp/rapids-cmake")
        # Use the local copy of rapids-cmake
        replace_in_file(self, "cmake/RAPIDS.cmake",
                        'FetchContent_Declare(rapids-cmake URL "${rapids-cmake-url}")',
                        'FetchContent_Declare(rapids-cmake URL "${CMAKE_SOURCE_DIR}/rapids-cmake")')
        # Prohibit FetchContent after loading rapids-cmake
        replace_in_file(self, "cpp/CMakeLists.txt",
                        "include(rapids-cmake)",
                        "include(rapids-cmake)\n"
                        "set(FETCHCONTENT_FULLY_DISCONNECTED 1)")
        # Don't force an exact CCCL version
        replace_in_file(self, "cpp/rapids-cmake/rapids-cmake/cpm/cccl.cmake", "FIND_PACKAGE_ARGUMENTS EXACT", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["RMM_NVTX"] = True
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["CPM_USE_LOCAL_PACKAGES"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "rmm")
        self.cpp_info.set_property("cmake_target_name", "rmm::rmm")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["RMM"])
        self.cpp_info.libs = ["rmm"]
        self.cpp_info.defines = [
            "LIBCUDACXX_ENABLE_EXPERIMENTAL_MEMORY_RESOURCE",
            "RMM_NVTX"
        ]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
        self.cpp_info.requires = [
            "rapids_logger::rapids_logger",
            "cudart::cudart_",
            "nvtx::nvtx",
        ]
