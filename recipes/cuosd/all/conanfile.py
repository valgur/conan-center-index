import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps

required_conan_version = ">=2.1"


class CuOSDConan(ConanFile):
    name = "cuosd"
    description = "cuOSD: CUDA On-Screen Display. Draw all elements using a single CUDA kernel."
    license = "MIT"
    homepage = "https://github.com/NVIDIA-AI-IOT/Lidar_AI_Solution/tree/master/libraries/cuOSD"
    topics = ("cuda", "visualization", "overlay", "nvidia")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "text_backend": ["pango", "stb", "none"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "text_backend": "stb",
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src/libraries/cuOSD"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart")
        if self.options.text_backend == "pango":
            self.requires("pango/[^1.54.0]")
        elif self.options.text_backend == "stb":
            self.requires("stb/[*]")

    def validate_build(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rm(self, "stb_*.h", "libraries/cuOSD/src/textbackend")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ENABLE_PANGO"] = self.options.text_backend == "pango"
        tc.cache_variables["ENABLE_STB"] = self.options.text_backend == "stb"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        deps = PkgConfigDeps(self)
        deps.generate()
        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="libraries/cuOSD")
        cmake.build()

    def _extract_license(self):
        content = Path(self.source_folder, "libraries/cuOSD/src/cuosd.h").read_text(encoding="utf-8")
        license = content.split(" */", 1)[0].replace("/*", "").replace(" * ", "").replace(" *", "").strip() + "\n"
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE.txt"), license)

    def package(self):
        self._extract_license()
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["cuosd"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.options.text_backend == "pango":
            self.cpp_info.requires.append("pango::pangocairo")
        elif self.options.text_backend == "stb":
            self.cpp_info.requires.append("stb::stb")
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m"]
