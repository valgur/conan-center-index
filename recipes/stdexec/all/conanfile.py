import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class StdexecConan(ConanFile):
    name = "stdexec"
    description = ("stdexec is an experimental reference implementation of the Senders model of asynchronous programming"
                   " proposed by P2300 - std::execution for adoption into the C++ Standard.")
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/stdexec"
    topics = ("c++26", "concurrency", "asynchronous", "senders", "execution", "header-only")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_cuda": [True, False],
        "enable_tbb": [True, False],
        "enable_taskflow": [True, False],
        "enable_asio": [False, "boost", "standalone"],
        "enable_numa": [True, False],
        "enable_libdispatch": [True, False],
    }
    default_options = {
        "header_only": True,
        "shared": False,
        "fPIC": True,
        "enable_cuda": False,
        "enable_tbb": False,
        "enable_taskflow": False,
        "enable_asio": False,
        "enable_numa": False,
        "enable_libdispatch": False,
    }
    implements = ["auto_header_only", "auto_shared_fpic"]
    no_copy_source = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Macos":
            del self.options.enable_libdispatch

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.enable_cuda:
            self.requires("cub/[^2.2]", transitive_headers=True, transitive_libs=True)
            self.requires("nvtx/[^3.0]", transitive_headers=True, transitive_libs=True)
        if self.options.enable_tbb:
            self.requires("onetbb/[>=2021]", transitive_headers=True, transitive_libs=True)
        if self.options.enable_taskflow:
            self.requires("taskflow/[^3.7]", transitive_headers=True, transitive_libs=True)
        if self.options.enable_asio == "boost":
            self.requires("boost/[^1.71]", transitive_headers=True, libs=False)
        elif self.options.enable_asio == "standalone":
            self.requires("asio/[^1.31]", transitive_headers=True)
        if self.options.enable_numa:
            self.requires("libnuma/[^2.0]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 20)
        # Also cuda_std_20

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25.0 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Let Conan set the C++ standard
        replace_in_file(self, "CMakeLists.txt", " CXX_STANDARD 20", " ")

    def generate(self):
        if not self.options.header_only:
            tc = CMakeToolchain(self)
            tc.cache_variables["STDEXEC_BUILD_TESTS"] = False
            tc.cache_variables["STDEXEC_BUILD_EXAMPLES"] = False
            tc.cache_variables["STDEXEC_BUILD_DOCS"] = False
            tc.generate()

    def build(self):
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def _write_version_header(self):
        v = Version(self.version)
        save(self, os.path.join(self.package_folder, "include", "stdexec_version_config.hpp"),
             "#pragma once\n"
             f"#define STDEXEC_VERSION_MAJOR {v.major}\n"
             f"#define STDEXEC_VERSION_MINOR {v.minor}\n"
             f"#define STDEXEC_VERSION_PATCH {v.patch}\n")

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.install()
            if self.options.enable_cuda:
                # Don't vendor CCCL
                rmdir(self, os.path.join(self.package_folder, "include", "rapids"))
                rmdir(self, os.path.join(self.package_folder, "lib", "rapids"))
        else:
            self._write_version_header()
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "stdexec")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["STDEXEC"])

        self.cpp_info.components["stdexec_core"].set_property("cmake_target_name", "STDEXEC::stdexec")
        self.cpp_info.components["stdexec_core"].libdirs = []
        self.cpp_info.components["stdexec_core"].bindirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["stdexec_core"].cxxflags.append("-pthread")
            self.cpp_info.components["stdexec_core"].sharedlinkflags.append("-pthread")
            self.cpp_info.components["stdexec_core"].exelinkflags.append("-pthread")
        if self.settings.compiler == "gcc":
            self.cpp_info.components["stdexec_core"].cxxflags.append("-fcoroutines")
            self.cpp_info.components["stdexec_core"].cxxflags.append("-fconcepts-diagnostics-depth=10")
        elif self.settings.compiler == "msvc":
            self.cpp_info.components["stdexec_core"].cxxflags.append("/Zc:__cplusplus")
            self.cpp_info.components["stdexec_core"].cxxflags.append("/Zc:preprocessor")
        if self.options.enable_numa:
            self.cpp_info.components["stdexec_core"].defines.append("STDEXEC_ENABLE_NUMA")
            self.cpp_info.components["stdexec_core"].requires.append("libnuma::libnuma")
        if self.options.get_safe("enable_libdispatch"):
            self.cpp_info.components["stdexec_core"].defines.append("STDEXEC_ENABLE_LIBDISPATCH")
            self.cpp_info.components["stdexec_core"].frameworks.append("Dispatch")

        if not self.options.header_only:
            self.cpp_info.components["system_context"].set_property("cmake_target_name", "STDEXEC::system_context")
            self.cpp_info.components["system_context"].libs = ["system_context"]
            self.cpp_info.components["system_context"].requires = ["stdexec_core"]

        if self.options.enable_cuda:
            self.cpp_info.components["nvexec"].set_property("cmake_target_name", "STDEXEC::nvexec")
            self.cpp_info.components["nvexec"].libdirs = []
            self.cpp_info.components["nvexec"].bindirs = []
            self.cpp_info.components["nvexec"].requires = ["stdexec_core", "cub::cub", "nvtx::nvtx"]
            # The consumer will need to take care of linking against the CUDA runtime themselves.
            # Also sets "-stdpar;-gpu=cc${CMAKE_CUDA_ARCHITECTURES}" cxxflags and ldflags if using NVHPC

        if self.options.enable_tbb:
            self.cpp_info.components["tbbpool"].set_property("cmake_target_name", "STDEXEC::tbbpool")
            self.cpp_info.components["tbbpool"].libdirs = []
            self.cpp_info.components["tbbpool"].bindirs = []
            self.cpp_info.components["tbbpool"].requires = ["stdexec_core", "onetbb::libtbb"]

        if self.options.enable_taskflow:
            self.cpp_info.components["taskflow_pool"].set_property("cmake_target_name", "STDEXEC::taskflow_pool")
            self.cpp_info.components["taskflow_pool"].libdirs = []
            self.cpp_info.components["taskflow_pool"].bindirs = []
            self.cpp_info.components["taskflow_pool"].requires = ["stdexec_core", "taskflow::taskflow"]

        if self.options.enable_asio:
            self.cpp_info.components["asio_pool"].set_property("cmake_target_name", "STDEXEC::asio_pool")
            self.cpp_info.components["asio_pool"].libdirs = []
            self.cpp_info.components["asio_pool"].bindirs = []
            if self.options.enable_asio == "boost":
                self.cpp_info.components["asioexec_boost"].set_property("cmake_target_name", "STDEXEC::asioexec_boost")
                self.cpp_info.components["asioexec_boost"].libdirs = []
                self.cpp_info.components["asioexec_boost"].bindirs = []
                self.cpp_info.components["asioexec_boost"].requires = ["stdexec_core", "boost::asio"]
                self.cpp_info.components["asio_pool"].requires = ["asioexec_boost"]
            elif self.options.enable_asio == "standalone":
                self.cpp_info.components["asioexec_asio"].set_property("cmake_target_name", "STDEXEC::asioexec_asio")
                self.cpp_info.components["asioexec_asio"].libdirs = []
                self.cpp_info.components["asioexec_asio"].bindirs = []
                self.cpp_info.components["asioexec_asio"].requires = ["stdexec_core", "asio::asio"]
                self.cpp_info.components["asio_pool"].requires = ["asioexec_asio"]
