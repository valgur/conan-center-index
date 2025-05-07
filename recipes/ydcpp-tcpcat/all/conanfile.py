import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc


class TcpcatConan(ConanFile):
    name = "ydcpp-tcpcat"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ydcpp/tcpcat"
    description = "Simple C++ TCP Server and Client library."
    topics = ("network", "tcp", "tcp-server", "tcp-client")
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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 17)

        # Upstream meant to support Windows Shared builds, but they don't currently export any symbols
        # Disable for now until fixed. As this is an upstream issue they want fixed, we don't set
        # package_type = "static-library" in the configure() method so that users have a clear message error for now
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} does not currently support Windows shared builds due to an upstream issue")

    def requirements(self):
        self.requires("asio/[>=1.30.2 <1.32]", transitive_headers = True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["ydcpp-tcpcat"]
        self.cpp_info.set_property("cmake_target_name", "ydcpp-tcpcat")
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs.append("m")
