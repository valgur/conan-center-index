import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PortFFTConan(ConanFile):
    name = "portfft"
    description = "portFFT is a library implementing Fast Fourier Transforms using SYCL"
    license = "Apache-2.0"
    homepage = "https://github.com/codeplaysoftware/portFFT"
    topics = ("fft", "dft", "sycl", "math", "gpgpu")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "log_dumps": [True, False],
        "log_traces": [True, False],
        "log_transfers": [True, False],
        "log_warnings": [True, False],
        "use_scla": [True, False],
        "use_sg_transfers": [True, False],
        "slow_sg_shuffles": [True, False],
        "registers_per_wi": ["ANY"],
        "subgroup_sizes": ["ANY"],
        "vec_load_bytes": ["ANY"],
        "sgs_in_wg": ["ANY"],
        "max_concurrent_kernels": ["ANY"],
        "device_triple": ["ANY"],
    }
    default_options = {
        "log_dumps": False,
        "log_traces": False,
        "log_transfers": False,
        "log_warnings": False,
        "use_scla": False,
        "use_sg_transfers": False,
        "slow_sg_shuffles": False,
        "registers_per_wi": 128,
        "subgroup_sizes": 32,
        "vec_load_bytes": 16,
        "sgs_in_wg": 2,
        "max_concurrent_kernels": 16,
        "device_triple": "spir64",
    }

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler != "intel-cc" or self.settings.compiler.mode == "classic":
            raise ConanInvalidConfiguration("Intel icpx or dpcpp compiler is required to use portFFT")
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        # Copy instead of calling cmake.install() since the installed layout is quite messy
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "portfft")
        self.cpp_info.set_property("cmake_target_name", "portfft::portfft")
        self.cpp_info.set_property("system_package_version", "0.1.0")

        self.cpp_info.defines = [
            f"PORTFFT_REGISTERS_PER_WI={self.options.registers_per_wi}",
            f"PORTFFT_SUBGROUP_SIZES={self.options.subgroup_sizes}",
            f"PORTFFT_VEC_LOAD_BYTES={self.options.vec_load_bytes}",
            f"PORTFFT_SGS_IN_WG={self.options.sgs_in_wg}",
            f"PORTFFT_MAX_CONCURRENT_KERNELS={self.options.max_concurrent_kernels}",
            f"PORTFFT_SLOW_SG_SHUFFLES={'1' if self.options.slow_sg_shuffles else '0'}",
        ]
        if self.options.use_sg_transfers:
            self.cpp_info.defines.append("PORTFFT_USE_SG_TRANSFERS")
        if self.options.use_scla:
            self.cpp_info.defines.append("PORTFFT_USE_SCLA")
        if self.options.log_dumps:
            self.cpp_info.defines.append("PORTFFT_LOG_DUMPS")
        if self.options.log_transfers:
            self.cpp_info.defines.append("PORTFFT_LOG_TRANSFERS")
        if self.options.log_traces:
            self.cpp_info.defines.append("PORTFFT_LOG_TRACES")
        if self.options.log_warnings:
            self.cpp_info.defines.append("PORTFFT_LOG_WARNINGS")
        if any([self.options.log_dumps, self.options.log_transfers, self.options.log_traces, self.options.log_warnings]):
            self.cpp_info.defines.append("PORTFFT_KERNEL_LOG")

        self.cpp_info.cxxflags = [
            "-fsycl",
            "-fsycl-device-code-split=per_kernel",
            f"-fsycl-targets={self.options.device_triple}",
            "-fsycl-unnamed-lambda"
        ]
        if self.settings.compiler.mode == "dpcpp":
            # Set by the project but not supported by icpx
            self.cpp_info.cxxflags.append("-fgpu-inline-threshold=1000000")
        self.cpp_info.sharedlinkflags = ["-fsycl-device-code-split=per_kernel"]
        self.cpp_info.exelinkflags = ["-fsycl-device-code-split=per_kernel"]
