import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class GemmlowpConan(ConanFile):
    name = "gemmlowp"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/gemmlowp"
    description = "Low-precision matrix multiplication"
    topics = ("gemm", "matrix")

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "contrib"))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "gemmlowp")
        self.cpp_info.set_property("cmake_target_name", "gemmlowp::gemmlowp")

        self.cpp_info.components["eight_bit_int_gemm"].set_property("cmake_target_name", "gemmlowp::eight_bit_int_gemm")
        self.cpp_info.components["eight_bit_int_gemm"].includedirs.append(os.path.join("include", "gemmlowp"))
        self.cpp_info.components["eight_bit_int_gemm"].libs = ["eight_bit_int_gemm"]
        if is_msvc(self):
            self.cpp_info.components["eight_bit_int_gemm"].defines = ["NOMINMAX"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["eight_bit_int_gemm"].system_libs.extend(["pthread"])
