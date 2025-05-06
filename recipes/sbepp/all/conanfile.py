import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "sbepp"
    description = "C++ implementation of the FIX Simple Binary Encoding"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/OleksandrKvl/sbepp"
    topics = ("trading", "fix", "sbe")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_sbeppc": [True, False],
    }
    default_options = {
        "with_sbeppc": True,
    }

    def export_sources(self):
        copy(self, os.path.join("cmake", "sbeppcTargets.cmake"), self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        if not self.info.options.with_sbeppc:
            self.info.clear()
        else:
            del self.info.settings.compiler

    def requirements(self):
        if self.options.with_sbeppc:
            self.requires("fmt/[>=9]")
            self.requires("pugixml/[^1.14]")

    def validate_build(self):
        check_min_cppstd(self, 17 if self.options.with_sbeppc else 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SBEPP_BUILD_SBEPPC"] = self.options.with_sbeppc
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENS.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        copy(self, "sbeppcTargets.cmake",
            src=os.path.join(self.source_folder, os.pardir, "cmake"),
            dst=os.path.join(self.package_folder, self._module_path))
        copy(self, "sbeppcHelpers.cmake",
            src=os.path.join(self.source_folder, "cmake"),
            dst=os.path.join(self.package_folder, self._module_path))

    @property
    def _module_path(self):
        return os.path.join("lib", "cmake")

    def package_info(self):
        # provide sbepp::sbeppc target and CMake helpers from sbeppcHelpers.cmake
        build_modules = [
            os.path.join(self._module_path, "sbeppcTargets.cmake"),
            os.path.join(self._module_path, "sbeppcHelpers.cmake"),
        ]

        self.cpp_info.builddirs.append(self._module_path)
        self.cpp_info.set_property("cmake_build_modules", build_modules)
