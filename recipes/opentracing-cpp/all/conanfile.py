# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir

required_conan_version = ">=1.53.0"


class OpenTracingConan(ConanFile):
    name = "opentracing-cpp"
    description = "C++ implementation of the OpenTracing API http://opentracing.io"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/opentracing/opentracing-cpp"
    topics = "opentracing"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_mocktracer": [True, False],
        "enable_dynamic_load": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_mocktracer": False,
        "enable_dynamic_load": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(self.name + "-" + self.version, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_MOCKTRACER"] = self.options.enable_mocktracer
        tc.variables["BUILD_DYNAMIC_LOADING"] = self.options.enable_dynamic_load
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["BUILD_TESTING"] = False
        tc.variables["ENABLE_LINTING"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "OpenTracing"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenTracing"

        target_suffix = "" if self.options.shared else "-static"
        lib_suffix = "" if self.options.shared or self.settings.os != "Windows" else "-static"
        # opentracing
        self.cpp_info.components["opentracing"].names["cmake_find_package"] = "opentracing" + target_suffix
        self.cpp_info.components["opentracing"].names["cmake_find_package_multi"] = (
            "opentracing" + target_suffix
        )
        self.cpp_info.components["opentracing"].libs = ["opentracing" + lib_suffix]
        if not self.options.shared:
            self.cpp_info.components["opentracing"].defines.append("OPENTRACING_STATIC")
        if self.options.enable_dynamic_load and self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["opentracing"].system_libs.append("dl")

        # opentracing_mocktracer
        if self.options.enable_mocktracer:
            self.cpp_info.components["opentracing_mocktracer"].names["cmake_find_package"] = (
                "opentracing_mocktracer" + target_suffix
            )
            self.cpp_info.components["opentracing_mocktracer"].names["cmake_find_package_multi"] = (
                "opentracing_mocktracer" + target_suffix
            )
            self.cpp_info.components["opentracing_mocktracer"].libs = ["opentracing_mocktracer" + lib_suffix]
            self.cpp_info.components["opentracing_mocktracer"].requires = ["opentracing"]
            if not self.options.shared:
                self.cpp_info.components["opentracing_mocktracer"].defines.append(
                    "OPENTRACING_MOCK_TRACER_STATIC"
                )
