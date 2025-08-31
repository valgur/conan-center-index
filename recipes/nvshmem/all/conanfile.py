import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvshmemConan(ConanFile):
    name = "nvshmem"
    description = ("NVSHMEM is a parallel programming interface based on OpenSHMEM that provides"
                   " efficient and scalable communication for NVIDIA GPU clusters.")
    license = "DocumentRef-License.txt:LicenseRef-NVSHMEM-License-Agreement AND BSD-3-Clause AND BSD-2-Clause AND mpich2"
    homepage = "https://developer.nvidia.com/nvshmem"
    topics = ("cuda", "shared-memory", "distributed-computing", "gpu-accelerated", "hpc")
    settings = "os", "arch", "compiler", "build_type", "cuda"
    # The library provides a purely static version `libnvshmem.a`, but a mixed `libnvshmem_host.so` and `libnvshmem_device.a`.
    # Forcing a package type breaks linkage due to CMakeDeps incorrectly setting the imported library types to SHARED/STATIC.
    # package_type = "library"
    options = {
        "build_bitcode_library": [True, False],
        "build_hydra_launcher": [True, False],
        "build_ibrc_transport": [True, False],
        "with_gdrcopy": [True, False],
        "with_libfabric": [True, False],
        "with_mlx5": [True, False],
        "with_mpi": [True, False],
        "with_nccl": [True, False],
        "with_pmix": [True, False],
        "with_ucx": [True, False],
    }
    default_options = {
        "build_bitcode_library": False,
        "build_hydra_launcher": False,
        "build_ibrc_transport": False,
        "with_gdrcopy": True,
        "with_libfabric": True,
        "with_mlx5": False,
        "with_mpi": False,
        "with_nccl": True,
        "with_pmix": False,
        "with_ucx": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if not any([
            self.options.build_ibrc_transport,
            self.options.with_mlx5,
            self.options.with_mlx5,
            self.options.with_libfabric,
            self.options.with_ucx,
        ]):
            self.options.with_gdrcopy.value = False
        if self.options.with_libfabric:
            self.options["libfabric"].shared = True
            self.options["libfabric"].cuda = True
            if self.options.with_gdrcopy:
                self.options["libfabric"].gdrcopy = True
            if self.options.with_ucx:
                self.options["libfabric"].ucx = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.cuda.version

    def requirements(self):
        self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
        self._utils.cuda_requires(self, "nvml-stubs")
        self.requires("nvtx/[^3]")
        if self.options.with_nccl:
            self.requires("nccl/[^2]")
        if self.options.with_gdrcopy:
            self.requires("gdrcopy/[^2.5]")
        if self.options.with_mlx5:
            self.requires("rdma-core/[*]", transitive_headers=True, options={"build_libmlx5": True})
        if self.options.with_libfabric:
            self.requires("libfabric/[>=1.21.0 <3]")
        if self.options.with_ucx:
            self.requires("openucx/[^1.19.0]", options={
                "cuda": True,
                "gdrcopy": self.options.with_gdrcopy,
                "mlx5": self.options.with_mlx5,
                "verbs": self.options.with_mlx5,
            })
        if self.options.with_mpi:
            self.requires("openmpi/[>=4 <6]", options={
                "with_cuda": True,
                "with_ucx": self.options.with_ucx,
            })
        if self.options.with_pmix:
            self.requires("openpmix/[*]")
        if self.options.build_bitcode_library:
            self.requires("curand/[^10]")

    def validate(self):
        if self.settings.compiler not in ["gcc", "clang"]:
            raise ConanInvalidConfiguration("NVSHMEM only supports compilation with GCC or Clang.")
        if self.options.with_libfabric and not self.dependencies["libfabric"].options.shared:
            # /usr/bin/ld: src/lib/nvshmem_transport_libfabric.so.3.0.0: version node not found for symbol fi_freeparams@@FABRIC_1.0
            # /usr/bin/ld: failed to set dynamic section sizes: bad value
            raise ConanInvalidConfiguration("libfabric/*:shared=True is required")
        check_min_cppstd(self, 11 if Version(self.settings.cuda.version) < 13 else 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.19 <5]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")
        if self.options.build_bitcode_library and self.settings.compiler != "clang":
            self.tool_requires("clang/[*]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_CUDA_COMPILER"] = "nvcc"
        tc.cache_variables["CMAKE_CUDA_ARCHITECTURES"] = self.settings.cuda.architectures.value.replace(",", ";")
        # Preferring tc.variables as these need to be passed to the src/device sub-project as well via the toolchain file.
        tc.variables["NVSHMEM_BUILD_PYTHON_LIB"] = False
        tc.variables["NVSHMEM_BUILD_EXAMPLES"] = False
        tc.variables["NVSHMEM_BUILD_TESTS"] = False
        tc.variables["NVSHMEM_BUILD_BITCODE_LIBRARY"] = self.options.build_bitcode_library
        tc.variables["NVSHMEM_BUILD_HYDRA_LAUNCHER"] = self.options.build_hydra_launcher
        tc.variables["NVSHMEM_IBDEVX_SUPPORT"] = self.options.with_mlx5
        tc.variables["NVSHMEM_IBGDA_SUPPORT"] = self.options.with_mlx5
        tc.variables["NVSHMEM_IBRC_SUPPORT"] = self.options.build_ibrc_transport
        tc.variables["NVSHMEM_LIBFABRIC_SUPPORT"] = self.options.with_libfabric
        tc.variables["NVSHMEM_MPI_SUPPORT"] = self.options.with_mpi
        tc.variables["NVSHMEM_NVTX"] = True
        tc.variables["NVSHMEM_PMIX_SUPPORT"] = self.options.with_pmix
        tc.variables["NVSHMEM_SHMEM_SUPPORT"] = self.options.with_mpi and self.options.with_ucx
        tc.variables["NVSHMEM_UCX_SUPPORT"] = self.options.with_ucx
        tc.variables["NVSHMEM_USE_GDRCOPY"] = self.options.with_gdrcopy
        tc.variables["NVSHMEM_USE_NCCL"] = self.options.with_nccl
        tc.variables["CUDA_HOME"] = self.dependencies.build["nvcc"].package_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("openmpi::oshmem", "cmake_target_name", "shmem")
        if self.options.build_bitcode_library and self.settings.compiler != "clang":
            deps.build_context_activated.append("clang")
        deps.generate()

        nvcc_tc = self._utils.NvccToolchain(self)
        nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "changelog", self.package_folder)
        rm(self, "git_commit.txt", self.package_folder)
        rm(self, "version.txt", self.package_folder)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "NVSHMEM")
        # Unofficial aggregate target
        self.cpp_info.set_property("cmake_target_name", "NVSHMEM::NVSHMEM")

        self.cpp_info.components["nvshmem_"].set_property("cmake_target_name", "nvshmem::nvshmem")
        self.cpp_info.components["nvshmem_"].libs = ["nvshmem"]
        self.cpp_info.components["nvshmem_"].requires = ["cudart::cudart_"]
        if self.options.with_nccl:
            self.cpp_info.components["nvshmem_"].requires.append("nccl::nccl")
        if self.settings.os == "Linux":
            self.cpp_info.components["nvshmem_"].system_libs = ["m", "dl", "pthread", "rt"]
        if stdcpp_library(self):
            # Need to link against C++ stdlib when using in a pure C project
            self.cpp_info.components["nvshmem_"].system_libs.append(stdcpp_library(self))

        # There's a caveat about using nvshmem_device in shared libraries:
        # https://docs.nvidia.com/nvshmem/api/using.html#building-nvshmem-applications-libraries

        self.cpp_info.components["nvshmem_device"].set_property("cmake_target_name", "nvshmem::nvshmem_device")
        self.cpp_info.components["nvshmem_device"].libs = ["nvshmem_device"]
        self.cpp_info.components["nvshmem_device"].requires = ["cudart::cudart_"]
        if self.options.with_nccl:
            self.cpp_info.components["nvshmem_device"].requires.append("nccl::nccl")

        self.cpp_info.components["nvshmem_host"].set_property("cmake_target_name", "nvshmem::nvshmem_host")
        self.cpp_info.components["nvshmem_host"].libs = ["nvshmem_host"]
        self.cpp_info.components["nvshmem_host"].requires = ["nvshmem_device", "cudart::cudart_", "nvml-stubs::nvml-stubs", "nvtx::nvtx"]
        if self.options.with_nccl:
            self.cpp_info.components["nvshmem_host"].requires.append("nccl::nccl")

        self.cpp_info.components["nvshmem_bootstrap_pmi"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_pmi")
        self.cpp_info.components["nvshmem_bootstrap_pmi"].libs = ["nvshmem_bootstrap_pmi.so"]

        self.cpp_info.components["nvshmem_bootstrap_pmi2"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_pmi2")
        self.cpp_info.components["nvshmem_bootstrap_pmi2"].libs = ["nvshmem_bootstrap_pmi2.so"]

        self.cpp_info.components["nvshmem_bootstrap_uid"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_uid")
        self.cpp_info.components["nvshmem_bootstrap_uid"].libs = ["nvshmem_bootstrap_uid.so"]

        if self.options.with_mpi:
            self.cpp_info.components["nvshmem_bootstrap_mpi"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_mpi")
            self.cpp_info.components["nvshmem_bootstrap_mpi"].libs = ["nvshmem_bootstrap_mpi.so"]
            self.cpp_info.components["nvshmem_bootstrap_mpi"].requires = ["openmpi::ompi-c"]

        if self.options.with_pmix:
            self.cpp_info.components["nvshmem_bootstrap_pmix"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_pmix")
            self.cpp_info.components["nvshmem_bootstrap_pmix"].libs = ["nvshmem_bootstrap_pmix.so"]
            self.cpp_info.components["nvshmem_bootstrap_pmix"].requires = ["openpmix::openpmix"]

        if self.options.with_mpi and self.options.with_ucx:
            self.cpp_info.components["nvshmem_bootstrap_shmem"].set_property("cmake_target_name", "nvshmem::nvshmem_bootstrap_shmem")
            self.cpp_info.components["nvshmem_bootstrap_shmem"].libs = ["nvshmem_bootstrap_shmem.so"]
            self.cpp_info.components["nvshmem_bootstrap_shmem"].requires = ["openmpi::oshmem"]

        if self.options.build_ibrc_transport:
            self.cpp_info.components["nvshmem_transport_ibrc"].set_property("cmake_target_name", "nvshmem::nvshmem_transport_ibrc")
            self.cpp_info.components["nvshmem_transport_ibrc"].libs = ["nvshmem_transport_ibrc.so"]
            self.cpp_info.components["nvshmem_transport_ibrc"].requires = ["cudart::cudart_"]
            if self.options.with_gdrcopy:
                self.cpp_info.components["nvshmem_transport_ibrc"].requires.append("gdrcopy::gdrcopy")

        if self.options.with_mlx5:
            self.cpp_info.components["nvshmem_transport_ibdevx"].set_property("cmake_target_name", "nvshmem::nvshmem_transport_ibdevx")
            self.cpp_info.components["nvshmem_transport_ibdevx"].libs = ["nvshmem_transport_ibdevx.so"]
            self.cpp_info.components["nvshmem_transport_ibdevx"].requires = ["cudart::cudart_", "rdma-core::libmlx5"]

        if self.options.with_mlx5:
            self.cpp_info.components["nvshmem_transport_ibgda"].set_property("cmake_target_name", "nvshmem::nvshmem_transport_ibgda")
            self.cpp_info.components["nvshmem_transport_ibgda"].libs = ["nvshmem_transport_ibgda.so"]
            self.cpp_info.components["nvshmem_transport_ibgda"].requires = ["cudart::cudart_", "rdma-core::libmlx5"]
            if self.options.with_gdrcopy:
                self.cpp_info.components["nvshmem_transport_ibgda"].requires.append("gdrcopy::gdrcopy")

        if self.options.with_libfabric:
            self.cpp_info.components["nvshmem_transport_libfabric"].set_property("cmake_target_name", "nvshmem::nvshmem_transport_libfabric")
            self.cpp_info.components["nvshmem_transport_libfabric"].libs = ["nvshmem_transport_libfabric.so"]
            self.cpp_info.components["nvshmem_transport_libfabric"].requires = ["cudart::cudart_", "libfabric::libfabric"]
            if self.options.with_gdrcopy:
                self.cpp_info.components["nvshmem_transport_libfabric"].requires.append("gdrcopy::gdrcopy")

        if self.options.with_ucx:
            self.cpp_info.components["nvshmem_transport_ucx"].set_property("cmake_target_name", "nvshmem::nvshmem_transport_ucx")
            self.cpp_info.components["nvshmem_transport_ucx"].libs = ["nvshmem_transport_ucx.so"]
            self.cpp_info.components["nvshmem_transport_ucx"].requires = ["openucx::openucx", "cudart::cudart_"]
            if self.options.with_gdrcopy:
                self.cpp_info.components["nvshmem_transport_ucx"].requires.append("gdrcopy::gdrcopy")

        if self.options.build_bitcode_library:
            # self.cpp_info.components["nvshmem_device_bitcode"].set_property("cmake_target_name", "nvshmem::nvshmem_bitcode")
            # self.cpp_info.components["nvshmem_device_bitcode"].libs = ["libnvshmem_device.bc"]
            self.cpp_info.components["nvshmem_device_bitcode"].requires = ["curand::curand"]

        for _, component in self.cpp_info.components.items():
            if "cudart::cudart_" in component.requires:
                component.defines.append("__STDC_LIMIT_MACROS")
                component.defines.append("__STDC_CONSTANT_MACROS")
