import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"

class FunctionsFrameworkCppConan(ConanFile):
    name = "functions-framework-cpp"
    description = "An open source FaaS (Functions as a Service) framework"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/GoogleCloudPlatform/functions-framework-cpp"
    topics = ("google", "cloud", "functions-as-a-service", "faas-framework")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
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

    def requirements(self):
        self.requires("abseil/[>=20220623.1]")
        self.requires("boost/[^1.71.0 <1.88]", options={"with_program_options": True})
        self.requires("nlohmann_json/[^3]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration("Fails to build for Visual Studio as a DLL")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["FUNCTIONS_FRAMEWORK_CPP_TEST_EXAMPLES"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        # Add a missing include
        path = Path(self.source_folder, "google/cloud/functions/internal/parse_options.cc")
        path.write_text("#include <cstdint>\n" + path.read_text())

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "functions_framework_cpp")
        self.cpp_info.set_property("cmake_target_name", "functions-framework-cpp::framework")
        self.cpp_info.set_property("pkg_config_name", "functions_framework_cpp")
        self.cpp_info.libs = ["functions_framework_cpp"]
        self.cpp_info.requires = [
            "abseil::absl_time",
            "boost::headers",
            "boost::program_options",
            "nlohmann_json::nlohmann_json",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
