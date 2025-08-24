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
        self.tool_requires("rapids-cmake/25.08.00")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["RMM_NVTX"] = True
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["CPM_USE_LOCAL_PACKAGES"] = True
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
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
