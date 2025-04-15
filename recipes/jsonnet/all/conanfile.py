import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library, valid_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class JsonnetConan(ConanFile):
    name = "jsonnet"
    description = "Jsonnet - The data templating language"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/jsonnet"
    topics = ("config", "json", "functional", "configuration")
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

    @property
    def _min_cppstd(self):
        return "11" if Version(self.version) < "0.20.0" else "17"

    @property
    def _compilers_minimum_version(self):
        return {
            "17": {
                "gcc": "8",
                "clang": "7",
                "apple-clang": "12",
                "msvc": "192",
            },
        }.get(self._min_cppstd, {})

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        if Version(self.version) == "0.17.0" and valid_min_cppstd(self, 17):
            raise ConanInvalidConfiguration(f"{self.ref} does not support C++{self.settings.compiler.cppstd}")

        if self.options.shared and is_msvc(self) and "d" in msvc_runtime_flag(self):
            raise ConanInvalidConfiguration(f"shared {self.ref} is not supported with MTd/MDd runtime")

        # This is a workround.
        # If jsonnet is shared, rapidyaml must be built as shared,
        # or the c4core functions that rapidyaml depends on will not be able to be found.
        # This seems to be a issue of rapidyaml.
        # https://github.com/conan-io/conan-center-index/pull/9786#discussion_r829887879
        if self.options.shared and Version(self.version) >= "0.18.0" and self.dependencies["rapidyaml"].options.shared == False:
            raise ConanInvalidConfiguration(f"shared {self.ref} requires rapidyaml to be built as shared")

    def requirements(self):
        self.requires("nlohmann_json/[^3]")
        if Version(self.version) >= "0.18.0":
            self.requires("rapidyaml/0.5.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["BUILD_SHARED_BINARIES"] = False
        tc.variables["BUILD_JSONNET"] = False
        tc.variables["BUILD_JSONNETFMT"] = False
        tc.variables["USE_SYSTEM_JSON"] = True
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        if not can_run(self):
            # Bypass https://github.com/google/jsonnet/blob/v0.20.0/stdlib/CMakeLists.txt,
            # which builds a simple native executable
            cxx = AutotoolsToolchain(self).vars().get("CXX_FOR_BUILD", "c++")
            self.run(f"{cxx} {os.path.join(self.source_folder, 'stdlib', 'to_c_array.cpp')} -o to_c_array")
            self.run(f"./to_c_array {os.path.join(self.source_folder, 'stdlib', 'std.jsonnet')} {os.path.join(self.source_folder, 'core', 'std.jsonnet.h')}")
            save(self, os.path.join(self.source_folder, "stdlib", "CMakeLists.txt"), "")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["libjsonnet"].libs = ["jsonnet"]
        self.cpp_info.components["libjsonnet"].requires = ["nlohmann_json::nlohmann_json"]
        if Version(self.version) >= "0.18.0":
            self.cpp_info.components["libjsonnet"].requires.append("rapidyaml::rapidyaml")

        if stdcpp_library(self):
            self.cpp_info.components["libjsonnet"].system_libs.append(stdcpp_library(self))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libjsonnet"].system_libs.append("m")

        self.cpp_info.components["libjsonnetpp"].libs = ["jsonnet++"]
        self.cpp_info.components["libjsonnetpp"].requires = ["libjsonnet"]
