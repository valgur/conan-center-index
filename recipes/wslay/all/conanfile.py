import os

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class WslayConan(ConanFile):
    name = "wslay"
    description = "The WebSocket library in C"
    topics = ("websockets", "rfc6455", "communication", "tcp")
    homepage = "https://tatsuhiro-t.github.io/wslay"
    url = "https://github.com/conan-io/conan-center-index"
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
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["WSLAY_STATIC"] = not self.options.shared
        tc.variables["WSLAY_SHARED"] = self.options.shared
        # Relocatable shared libs on macOS
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        if Version(self.version) > "1.1.1":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    @property
    def _wslay_lib_target(self):
        return "wslay_shared" if self.options.shared else "wslay"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "wslay")
        self.cpp_info.set_property("cmake_target_name", self._wslay_lib_target)
        self.cpp_info.set_property("pkg_config_name", "libwslay")
        self.cpp_info.libs = [self._wslay_lib_target]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]
