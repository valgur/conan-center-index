import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuDnnFrontendConan(ConanFile):
    name = "cudnn-frontend"
    description = "The cuDNN FrontEnd API is a C++ header-only library to the cuDNN C backend API."
    license = "MIT"
    homepage = "https://github.com/NVIDIA/cudnn-frontend"
    topics = ("cuda", "cudnn", "deep-learning", "neural-networks", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "with_json": [True, False],
    }
    default_options = {
        "with_json": True,
    }

    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        max_version = "9.11" if self.cuda.major < 12 else "10"
        self.requires(f"cudnn/[>=8.5.0 <{max_version}]")
        if self.options.with_json:
            self.requires("nlohmann_json/[^3]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Unvendor nlohmann_json
        rmdir(self, "include/cudnn_frontend/thirdparty")
        replace_in_file(self, "include/cudnn_frontend_utils.h",
                        '#include "cudnn_frontend/thirdparty/nlohmann/json.hpp"',
                        '#include <nlohmann/json.hpp>')

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cudnn_frontend")
        self.cpp_info.set_property("cmake_target_name", "cudnn_frontend")
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.requires = ["cudnn::cudnn_shim"]
        if self.options.with_json:
            self.cpp_info.requires.append("nlohmann_json::nlohmann_json")
        else:
            self.cpp_info.defines.append("CUDNN_FRONTEND_SKIP_JSON_LIB")
