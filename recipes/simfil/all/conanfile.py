import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SimfilRecipe(ConanFile):
    name = "simfil"
    description = "simfil is a C++ 17 library and a language for querying structured map feature data. The library provides an efficient in-memory storage pool for map data, optimized for the simfil query language, along with a query interpreter to query the actual data."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Klebert-Engineering/simfil"
    license = "BSD-3-Clause"
    package_type = "library"
    topics = ["query-language", "json", "data-model"]

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_json": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_json": True,
    }
    implements = ["auto_shared_fpic"]

    def validate(self):
        check_min_cppstd(self, 20)

    def build_requirements(self):
        self.tool_requires("cmake/[>3.19 <5]")

    def requirements(self):
        self.requires("sfl/[^1.2.4]", transitive_headers=True)
        self.requires("fmt/[>=5]", transitive_headers=True)
        self.requires("bitsery/[^5.2.3]", transitive_headers=True)
        if self.options.with_json:
            self.requires("nlohmann_json/[^3]", transitive_headers=True)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SIMFIL_CONAN"] = True
        tc.cache_variables["SIMFIL_SHARED"] = self.options.shared
        tc.cache_variables["SIMFIL_WITH_REPL"] = False
        tc.cache_variables["SIMFIL_WITH_COVERAGE"] = False
        tc.cache_variables["SIMFIL_WITH_TESTS"] = False
        tc.cache_variables["SIMFIL_WITH_EXAMPLES"] = False
        tc.cache_variables["SIMFIL_WITH_MODEL_JSON"] = self.options.with_json
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["simfil"]
        if self.options.with_json:
            self.cpp_info.defines = ["SIMFIL_WITH_MODEL_JSON=1"]
