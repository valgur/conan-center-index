import os

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class FlannConan(ConanFile):
    name = "flann"
    description = "Fast Library for Approximate Nearest Neighbors"
    topics = ("nns", "nearest-neighbor-search", "knn", "kd-tree")
    homepage = "https://www.cs.ubc.ca/research/flann/"
    license = "BSD-3-Clause"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cuda": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # see https://github.com/conan-io/conan-center-index/pull/16355#discussion_r1150197550
        self.requires("lz4/[^1.9.4]", transitive_headers=True, transitive_libs=True)
        # used in a public header:
        # https://github.com/flann-lib/flann/blob/1.9.2/src/cpp/flann/algorithms/nn_index.h#L323
        self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_cuda:
            self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if Version(self.version) >= "1.9.2":
            check_min_cppstd(self, 11)
        if self.options.with_cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # remove embedded lz4
        rmdir(self, "src/cpp/flann/ext")
        rmdir(self, "src/test")
        if Version(self.version) < "1.9.2":
            # Workaround issue with empty sources for a CMake target
            save(self, "src/cpp/empty.cpp", "\n")
            replace_in_file(self, "src/cpp/CMakeLists.txt",
                            'add_library(flann_cpp SHARED "")',
                            "add_library(flann_cpp SHARED empty.cpp)")
            replace_in_file(self, "src/cpp/CMakeLists.txt",
                            'add_library(flann SHARED "")',
                            "add_library(flann SHARED empty.cpp)")
        if Version(self.version) > "1.9.2":
            # Don't set CUDA arch flags, let NvccToolchain handle it
            replace_in_file(self, "src/cpp/CMakeLists.txt", " ;-gencode=", '") #')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_C_BINDINGS"] = True
        tc.variables["BUILD_CUDA_LIB"] = self.options.with_cuda
        # Only build the C++ libraries
        tc.variables["BUILD_DOC"] = False
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_MATLAB_BINDINGS"] = False
        tc.variables["BUILD_PYTHON_BINDINGS"] = False
        tc.variables["USE_OPENMP"] = True
        # Generate a relocatable shared lib on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support
        if Version(self.version) > "1.9.2":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()

        cd = CMakeDeps(self)
        cd.generate()

        if self.options.with_cuda:
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # Remove vc runtimes
        if self.settings.os == "Windows":
            if self.options.shared:
                for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
                    rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"))
            else:
                rmdir(self, os.path.join(self.package_folder, "bin"))
        # Remove static/dynamic libraries depending on the build mode
        libs_pattern_to_remove = ["_s.*"] if self.options.shared else ["*flann_cpp.*", "*flann.*", "*flann_cuda.*"]
        for lib_pattern_to_remove in libs_pattern_to_remove:
            rm(self, lib_pattern_to_remove, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_module_file_name", "Flann")
        self.cpp_info.set_property("cmake_file_name", "flann")
        self.cpp_info.set_property("pkg_config_name", "flann")

        suffix = "_s" if not self.options.shared else ""
        alias_suffix = "_s" if self.options.shared else ""

        # flann_cpp
        self.cpp_info.components["flann_cpp"].set_property("cmake_target_name", f"flann::flann_cpp{suffix}")
        self.cpp_info.components["flann_cpp"].set_property("cmake_target_aliases", [f"flann::flann_cpp{alias_suffix}"])
        self.cpp_info.components["flann_cpp"].libs = [f"flann_cpp{suffix}"]
        if not self.options.shared:
            self.cpp_info.components["flann_cpp"].defines = ["FLANN_STATIC"]
        self.cpp_info.components["flann_cpp"].requires = ["lz4::lz4", "openmp::openmp"]

        # flann
        self.cpp_info.components["flann_c"].set_property("cmake_target_name", f"flann::flann{suffix}")
        self.cpp_info.components["flann_c"].set_property("cmake_target_aliases", [f"flann::flann{alias_suffix}"])
        self.cpp_info.components["flann_c"].libs = [f"flann{suffix}"]
        if not self.options.shared:
            self.cpp_info.components["flann_c"].defines = ["FLANN_STATIC"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["flann_c"].system_libs = ["m"]
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.components["flann_c"].system_libs.append(stdcpp_library(self))
        self.cpp_info.components["flann_c"].requires = ["lz4::lz4", "openmp::openmp"]

        if self.options.with_cuda:
            self.cpp_info.components["flann_cuda"].set_property("cmake_target_name", f"flann::flann_cuda{suffix}")
            self.cpp_info.components["flann_cuda"].set_property("cmake_target_aliases", [f"flann::flann_cuda{alias_suffix}"])
            self.cpp_info.components["flann_cuda"].libs = [f"flann_cuda{suffix}"]
            if not self.options.shared:
                self.cpp_info.components["flann_cuda"].defines = ["FLANN_STATIC"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["flann_cuda"].system_libs = ["m"]
            self.cpp_info.components["flann_cuda"].requires = ["openmp::openmp", "cudart::cudart_"]
