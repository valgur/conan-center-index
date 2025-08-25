import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class JitifyConan(ConanFile):
    name = "jitify"
    description = "A single-header C++ library for simplifying the use of CUDA Runtime Compilation (NVRTC)"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVIDIA/jitify"
    topics = ("cuda", "jit", "nvrtc", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "v2": [True, False],
        "with_nvtx": [True, False],
    }
    default_options = {
        "v2": True,
        "with_nvtx": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if not self.options.v2:
            del self.options.with_nvtx

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.settings.clear()

    def requirements(self):
        self._utils.cuda_requires(self, "nvrtc")
        if self.options.v2:
            if Version(self.settings.cuda.version) >= "12.0":
                self._utils.cuda_requires(self, "nvjitlink")
            if self.options.with_nvtx:
                self._utils.cuda_requires(self, "nvtx")

    def validate(self):
        self._utils.validate_cuda_settings(self)
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "jitify.hpp", self.source_folder, os.path.join(self.package_folder, "include"))
        if self.options.v2:
            for f in [
                "jitify2.hpp",
                "jitify2_preprocess.cpp",
                "stringify.cpp",
            ]:
                copy(self, f, self.source_folder, os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        if self.options.v2:
            self.cpp_info.srcdirs = ["include"]
            if self.options.with_nvtx:
                self.cpp_info.defines.append("JITIFY_ENABLE_NVTX")
