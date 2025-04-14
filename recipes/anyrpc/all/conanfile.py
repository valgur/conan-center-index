import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class AnyRPCConan(ConanFile):
    name = "anyrpc"
    description = "A multiprotocol remote procedure call system for C++"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/sgieseking/anyrpc"
    topics = ("rpc",)

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_log4cplus": [True, False],
        "with_threading": [True, False],
        "with_regex": [True, False],
        "with_wchar": [True, False],
        "with_protocol_json": [True, False],
        "with_protocol_xml": [True, False],
        "with_protocol_messagepack": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_log4cplus": False,
        "with_threading": True,
        "with_wchar": True,
        "with_regex": True,
        "with_protocol_json": True,
        "with_protocol_xml": True,
        "with_protocol_messagepack": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_log4cplus:
            self.requires("log4cplus/2.0.7")

    def validate(self):
        check_min_cppstd(self, 11)

        if self.options.with_log4cplus and self.options.with_wchar:
            raise ConanInvalidConfiguration(
                f"{self.ref} cannot be built with both log4cplus and wchar, see"
                " https://github.com/sgieseking/anyrpc/issues/25"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ANYRPC_LIB_BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_TEST"] = False
        tc.variables["BUILD_WITH_ADDRESS_SANITIZE"] = False
        tc.variables["BUILD_WITH_LOG4CPLUS"] = self.options.with_log4cplus
        tc.variables["BUILD_WITH_THREADING"] = self.options.with_threading
        tc.variables["BUILD_WITH_REGEX"] = self.options.with_regex
        tc.variables["BUILD_WITH_WCHAR"] = self.options.with_wchar
        tc.variables["BUILD_PROTOCOL_JSON"] = self.options.with_protocol_json
        tc.variables["BUILD_PROTOCOL_XML"] = self.options.with_protocol_xml
        tc.variables["BUILD_PROTOCOL_MESSAGEPACK"] = self.options.with_protocol_messagepack
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        if Version(self.version) > "1.0.2":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="license", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["anyrpc"]
        if not self.options.shared and self.settings.os == "Windows":
            self.cpp_info.system_libs.append("ws2_32")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
