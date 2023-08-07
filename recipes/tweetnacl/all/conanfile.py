import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, download, save

required_conan_version = ">=1.53.0"


class TweetnaclConan(ConanFile):
    name = "tweetnacl"
    description = "TweetNaCl is the world's first auditable high-security cryptographic library"
    license = "Public domain"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://tweetnacl.cr.yp.to"
    topics = ("nacl", "encryption", "signature", "hashing")

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

    def export_sources(self):
        copy(self, "CMakeLists.txt",
             src=self.recipe_folder,
             dst=os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.shared and (self.settings.os == "Windows" or is_apple_os(self)):
            # needed for randombytes implementation
            self.requires("libsodium/cci.20220430")

    def source(self):
        for url_sha in self.conan_data["sources"][self.version]:
            download(self, **url_sha, filename=os.path.basename(url_sha["url"]))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = self.options.shared
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        save(self,
             os.path.join(self.package_folder, "licenses", "LICENSE"),
             "TweetNaCl is a self-contained public-domain C library.")
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["tweetnacl"]
