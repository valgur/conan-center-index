import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class OpenSimulationInterfaceConan(ConanFile):
    name = "open-simulation-interface"
    description = "Generic interface environmental perception of automated driving functions in virtual scenarios"
    license = "MPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/OpenSimulationInterface/open-simulation-interface"
    topics = ("asam", "adas", "open-simulation", "automated-driving", "openx")

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

    def requirements(self):
        self.requires("protobuf/[>=3.21.12]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.shared and self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "Shared Libraries are not supported on windows because of the missing symbol export in the library."
            )

    def build_requirements(self):
        self.tool_requires("protobuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.5)",
                        "cmake_minimum_required(VERSION 3.15)")
        if Version(self.version) < "3.7.0":
            replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 11)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        if self.settings.os == "Windows":
            rmdir(self, os.path.join(self.package_folder, "CMake"))
        else:
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "open_simulation_interface")
        self.cpp_info.set_property("cmake_target_name", "open_simulation_interface::open_simulation_interface")
        self.cpp_info.components["libopen_simulation_interface"].libs = ["open_simulation_interface"]
        self.cpp_info.components["libopen_simulation_interface"].requires = ["protobuf::libprotobuf"]
