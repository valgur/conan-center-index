import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import copy, get

required_conan_version = ">=2.1"


class ScipPlusPlus(ConanFile):
    name = "scippp"
    description = "SCIP++ is a C++ wrapper for SCIP's C interface"
    topics = ("mip", "solver", "linear", "programming")
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/scipopt/SCIPpp"
    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 17)

    def requirements(self):
        # see https://github.com/scipopt/SCIPpp/blob/1.0.0/conanfile.py#L25
        scip_version = self.conan_data["scip_mapping"][self.version]
        self.requires(f"scip/{scip_version}", transitive_headers=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.15.7 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # In upstream, the version is injected into CMake via git.
        tc.variables["scippp_version"] = self.version
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
        self.cpp_info.libs = ["ScipPP"]
