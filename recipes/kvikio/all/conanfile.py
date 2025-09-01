import os
from functools import cached_property

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class KvikIoConan(ConanFile):
    name = "kvikio"
    description = ("KvikIO is a C++ library for high performance file IO."
                   " It provides bindings to cuFile which enables GPUDirect Storage (GDS).")
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/kvikio"
    topics = ("cuda", "cufile", "io", "gds", "gpudirect-storage", "filesystem", "nvidia", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "remote_support": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "remote_support": True,
        "with_cuda": True,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("bshoshany-thread-pool/[^4.1.0]", transitive_headers=True)
        if self.options.remote_support:
            self.requires("libcurl/[>=7.78 <9]", transitive_headers=True)
        if self.options.with_cuda:
            self.cuda.requires("cufile", transitive_headers=True)
            self.cuda.requires("nvtx", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)
        self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_thread_pool.cmake", "find_package(bshoshany-thread-pool REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["KvikIO_BUILD_BENCHMARKS"] = False
        tc.cache_variables["KvikIO_BUILD_EXAMPLES"] = False
        tc.cache_variables["KvikIO_BUILD_TESTS"] = False
        tc.cache_variables["KvikIO_REMOTE_SUPPORT"] = self.options.remote_support
        tc.cache_variables["KvikIO_CUDA_SUPPORT"] = self.options.with_cuda
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("bshoshany-thread-pool", "cmake_target_name", "BS::thread_pool")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "kvikio")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["KVIKIO"])
        self.cpp_info.set_property("cmake_target_name", "kvikio::kvikio")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["kvikio"])
        self.cpp_info.libs = ["kvikio"]
        self.cpp_info.requires = ["bshoshany-thread-pool::bshoshany-thread-pool"]
        if self.options.remote_support:
            self.cpp_info.requires.append("libcurl::libcurl")
            self.cpp_info.defines.append("KVIKIO_LIBCURL_FOUND")
        if self.options.with_cuda:
            self.cpp_info.requires.append("cufile::cufile_")
            self.cpp_info.requires.append("nvtx::nvtx")
            self.cpp_info.defines.append("KVIKIO_CUDA_FOUND")
            self.cpp_info.defines.append("KVIKIO_CUFILE_FOUND")
            self.cpp_info.defines.append("KVIKIO_CUFILE_VERSION_API_FOUND")
            if self.dependencies["cufile"].ref.version >= "1.2":
                self.cpp_info.defines.append("KVIKIO_CUFILE_BATCH_API_FOUND")
            if self.dependencies["cufile"].ref.version >= "1.7":
                self.cpp_info.defines.append("KVIKIO_CUFILE_STREAM_API_FOUND")
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m", "dl"]
