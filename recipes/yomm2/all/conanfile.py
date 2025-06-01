import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class Yomm2Recipe(ConanFile):
    name = "yomm2"
    package_type = "header-library"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/jll63/yomm2"
    description = "Fast, orthogonal, open multi-methods. Solve the Expression Problem in C++17"
    topics = ("multi-methods", "multiple-dispatch", "open-methods", "shared-library",
              "header-only", "polymorphism", "expression-problem", "c++17")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
    }
    default_options = {
        "header_only": True
    }

    def configure(self):
        if not bool(self.options.header_only):
            self.package_type = "shared-library"

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.compiler == "apple-clang" and not bool(self.options.header_only):
            raise ConanInvalidConfiguration("Dynamic library builds are not supported on MacOS.")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.21 <5]")

    def requirements(self):
        self.requires("boost/[^1.71.0]", transitive_headers=True, libs=False)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) <= "1.5.1":
            replace_in_file(self, "CMakeLists.txt", "add_subdirectory(docs.in)", "")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["YOMM2_ENABLE_EXAMPLES"] = "OFF"
        tc.variables["YOMM2_ENABLE_TESTS"] = "OFF"
        tc.variables["YOMM2_SHARED"] = not bool(self.options.header_only)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package_id(self):
        # if yomm2 is built as static, it behaves as a header-only one
        if self.info.options.header_only:
            self.info.clear()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        if self.options.header_only:
            rmdir(self, os.path.join(self.package_folder, "lib"))
        else:
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "YOMM2")
        self.cpp_info.set_property("cmake_target_name", "YOMM2::yomm2")
        if self.options.header_only:
            self.cpp_info.bindirs = []
            self.cpp_info.libdirs = []
        else:  # shared-library
            self.cpp_info.libs = ["yomm2"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
