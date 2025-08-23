import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NvImageCodecConan(ConanFile):
    name = "nvimgcodec"
    description = ("The nvImageCodec is an open-source library of accelerated codecs with unified interface."
                   " It is designed as a framework for extension modules which delivers codec plugins.")
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/nvImageCodec"
    topics = ("cuda", "image", "codec")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "jpeg_turbo_ext": [True, False],
        "nvbmp_ext": [True, False],
        "nvjpeg2k_ext": [True, False],
        "nvjpeg_ext": [True, False],
        "nvpnm_ext": [True, False],
        "nvtiff_ext": [True, False],
        "opencv_ext": [True, False],
        "tiff_ext": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "jpeg_turbo_ext": False,
        "nvbmp_ext": False,
        "nvjpeg2k_ext": True,
        "nvjpeg_ext": True,
        "nvpnm_ext": False,
        "nvtiff_ext": True,
        "opencv_ext": False,
        "tiff_ext": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71]", libs=False)
        self.requires("nvtx/[^3]")
        self.requires("dlpack/[^1]")
        self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
        if self.settings.os == "Linux":
            self._utils.cuda_requires(self, "culibos")
        if self.options.jpeg_turbo_ext:
            self.requires("libjpeg-meta/latest")
        if self.options.tiff_ext:
            self.requires("libtiff/[^4.5.1]")
        if self.options.nvjpeg_ext:
            self._utils.cuda_requires(self, "nvjpeg", libs=False)
        if self.options.nvjpeg2k_ext:
            self._utils.cuda_requires(self, "nvjpeg2k")
        if self.options.nvtiff_ext:
            self._utils.cuda_requires(self, "nvtiff")
        if self.options.opencv_ext:
            self.requires("opencv/[^4.9]")

    def validate_build(self):
        check_min_cppstd(self, 20)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Respect the cuda.architectures setting
        replace_in_file(self, "CMakeLists.txt", "CUDA_find_supported_arch_values(", "# CUDA_find_supported_arch_values(")
        replace_in_file(self, "CMakeLists.txt", "CUDA_get_cmake_cuda_archs(", "# CUDA_get_cmake_cuda_archs(")
        replace_in_file(self, "extensions/nvjpeg/CMakeLists.txt", "CUDAToolkit_INCLUDE_DIRS", "nvjpeg_INCLUDE_DIRS")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_LIBJPEG_TURBO_EXT"] = self.options.jpeg_turbo_ext
        tc.cache_variables["BUILD_LIBTIFF_EXT"] = self.options.tiff_ext
        tc.cache_variables["BUILD_NVBMP_EXT"] = self.options.nvbmp_ext
        tc.cache_variables["BUILD_NVJPEG_EXT"] = self.options.nvjpeg_ext
        tc.cache_variables["BUILD_NVJPEG2K_EXT"] = self.options.nvjpeg2k_ext
        tc.cache_variables["BUILD_NVPNM_EXT"] = self.options.nvpnm_ext
        tc.cache_variables["BUILD_NVTIFF_EXT"] = self.options.nvtiff_ext
        tc.cache_variables["BUILD_OPENCV_EXT"] = self.options.opencv_ext
        tc.cache_variables["WITH_DYNAMIC_CUDA"] = False
        tc.cache_variables["WITH_DYNAMIC_NVJPEG"] = False
        tc.cache_variables["WITH_DYNAMIC_NVJPEG2K"] = False
        tc.cache_variables["WITH_DYNAMIC_NVTIFF"] = False
        tc.cache_variables["BUILD_PYTHON"] = False
        tc.cache_variables["BUILD_TEST"] = False
        tc.cache_variables["BUILD_SAMPLES"] = False
        tc.cache_variables["NVIMGCODEC_BUILD_DLPACK"] = False
        tc.cache_variables["NVIMGCODEC_BUILD_PYBIND11"] = False
        tc.cache_variables["CUDA_targeted_archs"] = ";"
        tc.cache_variables["ZSTD_LIBRARY"] = "zstd::libzstd"
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.cache_variables["NVJPEG_LOSSLESS_SUPPORTED"] = True
        if self.settings.os == "Linux" and not cross_building(self):
            tc.cache_variables["CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES"] = "/usr/include"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("zstd", "cmake_target_name", "zstd::libzstd")
        deps.generate()

        nvcc_tc = self._utils.NvccToolchain(self)
        nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "Acknowledgements.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "samples"))
        if self.options.shared:
            rm(self, "*_static.*", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*.so*", os.path.join(self.package_folder, "lib"))
            rm(self, "*nvimgcodec.*", os.path.join(self.package_folder, "lib"))
            rm(self, "*.dll", os.path.join(self.package_folder, "bin"))
            rmdir(self, os.path.join(self.package_folder, "extensions"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvimgcodec")
        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""
        self.cpp_info.components["nvimgcodec_"].set_property("cmake_target_name", f"nvimgcodec::nvimgcodec{suffix}")
        self.cpp_info.components["nvimgcodec_"].set_property("cmake_target_aliases", [f"nvimgcodec::nvimgcodec{alias_suffix}"])
        self.cpp_info.components["nvimgcodec_"].libs = [f"nvimgcodec{suffix}"]
        self.cpp_info.components["nvimgcodec_"].requires = [
            "boost::boost",
            "dlpack::dlpack",
            "nvtx::nvtx",
            "cudart::cudart_",
        ]
        if self.settings.os == "Linux":
            self.cpp_info.components["nvimgcodec_"].requires.append("culibos::culibos")
            self.cpp_info.components["nvimgcodec_"].system_libs = ["m", "dl"]

        def add_extension(name, requires=None):
            if not self.options.get_safe(name):
                return
            if self.options.shared or self.settings.os == "Windows":
                # The shared modules should not be used for linking
                self.cpp_info.components["_ext_requires"].requires.extend(requires or [])
                return
            comp = self.cpp_info.components[name]
            comp.set_property("cmake_target_name", f"nvimgcodec::{name}_static")
            comp.libs = [f"{name}_static"]
            comp.requires = requires or []
            if self.settings.os == "Linux":
                comp.system_libs = ["m", "dl"]

        add_extension("jpeg_turbo_ext", requires=["libjpeg-meta::libjpeg-meta"])
        add_extension("nvbmp_ext")
        add_extension("nvjpeg2k_ext", requires=["nvjpeg2k::nvjpeg2k"])
        add_extension("nvjpeg_ext", requires=["nvjpeg::nvjpeg"])
        add_extension("nvpnm_ext")
        add_extension("nvtiff_ext", requires=["nvtiff::nvtiff"])
        add_extension("opencv_ext", requires=["nvimgcodec_", "opencv::opencv"])
        add_extension("tiff_ext", requires=["libtiff::libtiff"])

        if self.options.shared:
            self.runenv_info.prepend_path("NVIMGCODEC_EXTENSIONS_PATH", os.path.join(self.package_folder, "extensions"))
