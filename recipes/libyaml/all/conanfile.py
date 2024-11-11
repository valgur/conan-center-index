from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.microsoft import is_msvc
import os

required_conan_version = ">=1.54.0"


class LibYAMLConan(ConanFile):
    name = "libyaml"
    description = "LibYAML is a YAML parser and emitter library."
    topics = ("yaml", "parser", "emitter")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/yaml/libyaml"
    license = "MIT"

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

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["INSTALL_CMAKE_DIR"] = "lib/cmake/libyaml"
        tc.variables["YAML_STATIC_LIB_NAME"] = "yaml"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # 0.2.2 has LICENSE, 0.2.5 has License, so ignore case
        copy(self, pattern="License", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"), ignore_case=True)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "yaml")
        self.cpp_info.set_property("cmake_target_name", "yaml")
        self.cpp_info.libs = ["yaml"]
        if is_msvc(self):
            self.cpp_info.defines = [
                "YAML_DECLARE_EXPORT" if self.options.shared
                else "YAML_DECLARE_STATIC"
            ]
