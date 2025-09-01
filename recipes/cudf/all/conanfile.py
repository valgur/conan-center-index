import os
from functools import cached_property

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CuDfConan(ConanFile):
    name = "cudf"
    description = "cuDF - GPU DataFrame Library"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cudf"
    topics = ("data-science", "gpu", "arrow", "cuda", "pandas", "data-analysis", "dask", "dataframe", "rapids", "nvidia")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "nanoarrow/*:with_cuda": True,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("nvcomp")
        self.cuda.requires("nvtx", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cucollections", transitive_headers=True, transitive_libs=True)
        self.requires("bshoshany-thread-pool/[^4.1.0]", transitive_headers=True, transitive_libs=True)
        self.requires("dlpack/[^1]")
        self.requires("flatbuffers/[~24.3.25]")
        self.requires("jitify/[^2]")
        self.requires("kvikio/[*]")
        self.requires("nanoarrow/[<1]")
        self.requires("rapids_logger/[<1]", transitive_headers=True, transitive_libs=True)
        self.requires("rmm/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("zlib-ng/[^2.0]")
        self.requires("zstd/[^1.5]")

    def validate(self):
        check_min_cppstd(self, 20)
        self.cuda.validate_settings()
        self.cuda.require_shared_deps(["nvrtc"])

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.10.00-git.20250822")
        self.tool_requires("jitify/<host_version>")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")

        for name, content in [
            ("cccl", "find_package(CCCL REQUIRED)"),
            ("cucollections", "find_package(cuco REQUIRED)"),
            ("dlpack", "find_package(dlpack REQUIRED)"),
            ("flatbuffers", "find_package(flatbuffers REQUIRED)"),
            ("jitify", "find_package(jitify REQUIRED)"),
            ("kvikio", "find_package(kvikio REQUIRED)"),
            ("nanoarrow", "find_package(nanoarrow REQUIRED)"),
            ("nvbench", "find_package(nvbench REQUIRED)"),
            ("nvcomp", "find_package(nvcomp REQUIRED)"),
            ("nvtx", "find_package(CUDAToolkit REQUIRED)"),
            ("rmm", "find_package(rmm REQUIRED)"),
            ("thread_pool", "find_package(bshoshany-thread-pool REQUIRED)"),
            ("zstd", "find_package(zstd REQUIRED)"),
        ]:
            save(self, f"cpp/cmake/thirdparty/get_{name}.cmake", content + "\n")

        # LD_LIBRARY_PATH is covered by Conan
        replace_in_file(self, "cpp/cmake/Modules/JitifyPreprocessKernels.cmake",
                        "LD_LIBRARY_PATH=${CUDAToolkit_LIBRARY_DIR}", "")
        # Don't remove '#pragma once' - fails with multiple definition errors
        replace_in_file(self, "cpp/cmake/Modules/JitifyPreprocessKernels.cmake", " --no-replace-pragma-once", "")
        replace_in_file(self, "cpp/cmake/Modules/JitifyPreprocessKernels.cmake",
                        "CUDAToolkit_INCLUDE_DIRS",
                        "CUDAToolkit_INCLUDE_DIRS libcudacxx_INCLUDE_DIRS cudart_INCLUDE_DIRS nvrtc_INCLUDE_DIRS")

        # Add missing includes
        extra_targets = [
            "nvcomp::nvcomp",
            "jitify::jitify",
            "dlpack::dlpack",
            "flatbuffers::flatbuffers",
        ]
        replace_in_file(self, "cpp/CMakeLists.txt", "nvcomp::nvcomp", " ".join(extra_targets))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["USE_NVTX"] = True
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["CUDF_BUILD_TESTUTIL"] = False
        tc.cache_variables["CUDF_BUILD_STREAMS_TEST_UTIL"] = False
        tc.cache_variables["JITIFY_USE_CACHE"] = True
        tc.cache_variables["CUDF_EXPORT_NVCOMP"] = False
        tc.cache_variables["CUDF_KVIKIO_REMOTE_IO"] = self.dependencies["kvikio"].options.remote_support
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["rapids-cmake-dir"] = self.dependencies.build["rapids-cmake"].cpp_info.builddirs[0].replace("\\", "/")
        tc.preprocessor_definitions["ZSTD_STATIC_LINKING_ONLY"] = ""
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("bshoshany-thread-pool", "cmake_target_name", "BS::thread_pool")
        deps.set_property("flatbuffers", "cmake_target_name", "flatbuffers::flatbuffers")
        deps.set_property("zstd", "cmake_target_name", "zstd")
        deps.set_property("nanoarrow", "cmake_target_name", "nanoarrow")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

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
        self.cpp_info.set_property("cmake_file_name", "cudf")
        self.cpp_info.set_property("cmake_target_name", "cudf::cudf")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["CUDF"])
        self.cpp_info.libs = ["cudf"]
