import os

from conan import ConanFile
from conan.tools import files
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout

required_conan_version = ">=2.1"


class Tixi3Conan(ConanFile):
    name = "tixi3"
    url = "https://github.com/conan-io/conan-center-index"
    description = "A simple xml interface based on libxml2 and libxslt"
    topics = ("xml", "xml2", "xslt")
    homepage = "https://github.com/DLR-SC/tixi"
    license = "Apache-2.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["TIXI_BUILD_EXAMPLES"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def requirements(self):
        self.requires("libxml2/[^2.12.5]")
        self.requires("libxslt/1.1.42")
        self.requires("libcurl/[>=7.78.0 <9]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # tixi is a c library
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def export_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            files.copy(self, patch["patch_file"], src=self.recipe_folder, dst=self.export_sources_folder)

    def source(self):
        files.get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        files.apply_conandata_patches(self)

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        files.rmdir(self, os.path.join(self.package_folder, "lib", "tixi3"))
        files.copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        files.rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tixi3")
        self.cpp_info.set_property("cmake_target_name", "tixi3")

        self.cpp_info.includedirs.append(os.path.join("include", "tixi3"))

        if self.settings.build_type != "Debug":
            self.cpp_info.libs = ["tixi3"]
        else:
            self.cpp_info.libs = ["tixi3-d"]

        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["shlwapi"]

        self.cpp_info.frameworks.extend(["Foundation"])
