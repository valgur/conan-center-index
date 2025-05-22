import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NovatelEdieConan(ConanFile):
    name = "novatel_edie"
    description = ("EDIE (Encode Decode Interface Engine) is a C++ SDK that can encode and decode messages "
                   "from NovAtel's OEM7 receivers from one format into another.")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/novatel/novatel_edie"
    topics = ("gnss", "novatel")
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

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            self.options["spdlog"].shared = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("nlohmann_json/[^3.11]", transitive_headers=True)
        self.requires("spdlog/[^1.10]", transitive_headers=True, transitive_libs=True)
        self.requires("gegles-spdlog_setup/[^1.1]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

        if self.options.shared and not self.dependencies["spdlog"].options.shared:
            # Statically linking against spdlog causes its singleton registry to be
            # re-instantiated in each shared library and executable that links against it.
            raise ConanInvalidConfiguration("spdlog must be dynamically linked when building novatel_edie as a shared library")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_TESTS"] = False
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
        rmdir(self, os.path.join(self.source_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "novatel_edie")
        self.cpp_info.set_property("cmake_target_name", "novatel_edie::novatel_edie")

        self.cpp_info.resdirs = ["share"]
        # Note: the order of the listed libs matters when linking statically.
        self.cpp_info.libs = [
            "edie_oem_decoder",
            "edie_decoders_common",
            "edie_common",
        ]

        db_path = os.path.join(self.package_folder, "share", "novatel_edie", "database.json")
        self.runenv_info.define_path("EDIE_DATABASE_FILE", db_path)
