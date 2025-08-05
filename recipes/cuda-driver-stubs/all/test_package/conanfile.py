import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps"

    _test_FindCUDAToolkit = False

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)
        if self._test_FindCUDAToolkit:
            for pkg in ["cudart", "cublas", "cufile", "cufft", "curand", "cusolver", "cusparse", "cupti", "npp",
                        "nvjpeg", "nvml-stubs", "nvptxcompiler", "nvrtc", "nvjitlink", "nvfatbin", "nvtx", "cuda-opencl"]:
                self.requires(f"{pkg}/[*]")

    def build_requirements(self):
        if self._test_FindCUDAToolkit:
            self.tool_requires("nvcc/[*]")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
