import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"

class LibuclConan(ConanFile):
    name = "libucl"
    description = "Universal configuration library parser"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/vstakhov/libucl"
    topics = ("universal", "configuration", "language", "parser", "ucl")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_url_include": [True, False],
        "enable_url_sign": [True, False],
        "with_lua": [False, "lua", "luajit"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_url_include": False,
        "enable_url_sign": False,
        "with_lua": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.enable_url_include:
            self.requires("libcurl/[>=7.78.0 <9]")
        if self.options.enable_url_sign:
            self.requires("openssl/[>=1.1 <4]")
        if self.options.with_lua == "lua":
            self.requires("lua/[^5.4.6]")
        elif self.options.with_lua == "luajit":
            self.requires("luajit/2.0.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        on_off = lambda v: "ON" if v else "OFF"
        tc.variables["ENABLE_URL_INCLUDE"] = on_off(self.options.enable_url_include)
        tc.variables["ENABLE_URL_SIGN"] = on_off(self.options.enable_url_sign)
        tc.variables["ENABLE_LUA"] = on_off(self.options.with_lua == "lua")
        tc.variables["ENABLE_LUAJIT"] = on_off(self.options.with_lua == "luajit")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["ucl"]
        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.defines.append("UCL_STATIC")

        self.cpp_info.set_property("pkg_config_name", "libucl")

        if Version(self.version) >= "0.9.0" and self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
