import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class KinetoConan(ConanFile):
    name = "kineto"
    description = "Kineto: A CPU+GPU Profiling library that provides access to timeline traces and hardware performance counters."
    license = "BSD-3-Clause"
    homepage = "https://github.com/pytorch/kineto"
    topics = ("gpu", "profiling", "cuda", "rocm", "intel", "pytorch")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cupti": [True, False],
        "with_roctracer": [True, False],
        "with_xpupti": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cupti": True,
        "with_roctracer": False,
        "with_xpupti": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/[*]")
        self.requires("dynolog/0.5.1-git.20250624")
        if self.options.with_cupti:
            self._utils.cuda_requires(self, "cupti", transitive_headers=True, transitive_libs=True)
        if self.options.with_roctracer:
            raise ConanInvalidConfiguration("ROCm support is not implemented yet")
        if self.options.with_xpupti:
            raise ConanInvalidConfiguration("Intel oneAPI support is not implemented yet")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.with_cupti:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Unvendor dynolog and fmt
        replace_in_file(self, "libkineto/CMakeLists.txt",
                        'add_subdirectory("${IPCFABRIC_INCLUDE_DIR}")',
                        "find_package(dynolog REQUIRED)\n"
                        "include_directories(${dynolog_INCLUDE_DIRS} ${dynolog_INCLUDE_DIRS}/dynolog/src/ipcfabric)\n"
                        "find_package(fmt REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["KINETO_LIBRARY_TYPE"] = "shared" if self.options.shared else "static"
        tc.cache_variables["KINETO_BUILD_TESTS"] = False
        tc.cache_variables["LIBKINETO_NOCUPTI"] = not self.options.with_cupti
        tc.cache_variables["LIBKINETO_NOROCTRACER"] = not self.options.with_roctracer
        tc.cache_variables["LIBKINETO_NOXPUPTI"] = not self.options.with_xpupti
        if self.options.with_cupti:
            tc.cache_variables["CUPTI_INCLUDE_DIR"] = self.dependencies["cupti"].cpp_info.includedir.replace("\\", "/")
            tc.cache_variables["CUDA_cupti_LIBRARY"] = "CUDA::cupti"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("fmt", "cmake_target_name", "fmt::fmt-header-only")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="libkineto")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))  # CMake config

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "kinetoLibrary")
        self.cpp_info.set_property("cmake_target_name", "kineto")
        self.cpp_info.libs = ["kineto"]
        self.cpp_info.requires = ["fmt::fmt", "dynolog::dynolog"]
        self.cpp_info.defines = ["KINETO_NAMESPACE=libkineto", "ENABLE_IPC_FABRIC"]
        if self.options.with_cupti:
            self.cpp_info.requires.append("cupti::cupti")
            self.cpp_info.defines.extend(["HAS_CUPTI", "USE_CUPTI_RANGE_PROFILER"])
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl", "pthread"]
