import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=2.1"


class LibProtobufMutatorConan(ConanFile):
    name = "libprotobuf-mutator"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/libprotobuf-mutator"
    description = "A library to randomly mutate protobuffers."
    topics = ("test", "fuzzing", "protobuf")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.get_safe("shared"):
            self.options.rm_safe("fPIC")
        if is_msvc(self):
            self.options.rm_safe("shared")
            self.package_type = "static-library"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Protobuf headers are required by public src/binary_format.h
        if self.version == "1.3":
            self.requires("protobuf/[^5.27.0]", transitive_headers=True)
        else:
            self.requires("protobuf/[>=5.27.0]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Preserves Conan as dependency manager
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/external)", "")
        # Use the correct target for linking
        replace_in_file(self, os.path.join("src", "CMakeLists.txt"), "${Protobuf_LIBRARIES}", "protobuf::libprotobuf")
        # Do not include examples when running CMake configure to avoid more dependencies
        save(self, os.path.join("examples", "CMakeLists.txt"), "")
        if self.version == "1.3":
            # Honor C++ standard from Conan
            replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 14)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIB_PROTO_MUTATOR_TESTING"] = False
        tc.variables["LIB_PROTO_MUTATOR_DOWNLOAD_PROTOBUF"] = False
        tc.variables["LIB_PROTO_MUTATOR_WITH_ASAN"] = False
        tc.variables["PKG_CONFIG_PATH"] = "share"
        if is_msvc(self):
            tc.variables["LIB_PROTO_MUTATOR_MSVC_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
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
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libprotobuf-mutator")
        self.cpp_info.set_property("cmake_target_name", "libprotobuf-mutator::libprotobuf-mutator")
        self.cpp_info.set_property("pkg_config_name", "libprotobuf-mutator")

        self.cpp_info.components["mutator"].libs = ["protobuf-mutator"]
        self.cpp_info.components["mutator"].set_property("cmake_target_name", "libprotobuf-mutator::protobuf-mutator")
        self.cpp_info.components["mutator"].includedirs.append(os.path.join("include", "libprotobuf-mutator"))
        self.cpp_info.components["mutator"].requires = ["protobuf::libprotobuf"]

        self.cpp_info.components["fuzzer"].libs = ["protobuf-mutator-libfuzzer"]
        self.cpp_info.components["fuzzer"].set_property("cmake_target_name", "libprotobuf-mutator::protobuf-mutator-libfuzzer")
        self.cpp_info.components["fuzzer"].includedirs.append(os.path.join("include", "libprotobuf-mutator"))
        self.cpp_info.components["fuzzer"].requires = ["mutator", "protobuf::libprotobuf"]
