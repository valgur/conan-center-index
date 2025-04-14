import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"

class MsgpackCConan(ConanFile):
    name = "msgpack-c"
    description = "MessagePack implementation for C"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/msgpack/msgpack-c"
    topics = ("msgpack", "message-pack", "serialization")
    package_type = "library"
    settings = "os", "arch", "build_type", "compiler"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MSGPACK_ENABLE_SHARED"] = self.options.shared
        tc.variables["MSGPACK_ENABLE_STATIC"] = not self.options.shared
        tc.variables["MSGPACK_32BIT"] = self.settings.arch == "x86"
        tc.variables["MSGPACK_BUILD_EXAMPLES"] = False
        tc.cache_variables["MSGPACK_BUILD_TESTS"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE_1_0.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "msgpack")
        self.cpp_info.set_property("pkg_config_name", "msgpack")
        if Version(self.version) < "6.0.0":
            self.cpp_info.libs = ["msgpackc"]
            self.cpp_info.set_property("cmake_target_name", "msgpackc")
        else:
            self.cpp_info.libs = ["msgpack-c"]
            self.cpp_info.set_property("cmake_target_name", "msgpack-c")
