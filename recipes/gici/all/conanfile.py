import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GiciConan(ConanFile):
    name = "gici"
    description = ("GNSS/INS/Camera Integrated Navigation Library (GICI-LIB) is a software package "
                   "for Global Navigation Satellite System (GNSS), Inertial Navigation System (INS), "
                   "and Camera integrated navigation.")
    license = "GPL-3.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/chichengcn/gici-open"
    topics = ("gnss", "navigation", "state-estimation", "factor-graphs", "rtk", "ppp", "ins", "visual-odometry")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Used in a public header in gici/imu/imu_types.h
        self.requires("eigen/3.4.0", transitive_headers=True, transitive_libs=True)
        # svo/common/types.h
        self.requires("opencv/[^4.5]", transitive_headers=True, transitive_libs=True)
        # gici/utility/option.h
        self.requires("yaml-cpp/0.8.0", transitive_headers=True, transitive_libs=True)
        # gici/utility/option.h
        self.requires("glog/0.6.0", transitive_headers=True, transitive_libs=True)
        # gici/imu/imu_error.h
        self.requires("ceres-solver/2.1.0", transitive_headers=True, transitive_libs=True)  # 2.2.0 is not compatible

    def validate(self):
        if self.settings.os != "Linux":
            # stream/streamer.cpp includes linux/videodev2.h
            raise ConanInvalidConfiguration(f"{self.name} only supports Linux")
        # code_bias.h fails with unordered_map constructor errors on C++17
        check_min_cppstd(self, 20)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=Path(self.source_folder).parent)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # The project does not export any CMake config or pkg-config files.
        self.cpp_info.libs = ["gici"]
        self.cpp_info.resdirs = ["res"]

        # Vendored libs
        self.cpp_info.includedirs.append(os.path.join("include", "gici", "third_party"))
        self.cpp_info.libs.extend(["rtklib", "vikit_common", "svo", "fast"])

        # Unofficial, for convenience
        self.runenv_info.define_path("GICI_DATA", os.path.join(self.package_folder, "res"))
