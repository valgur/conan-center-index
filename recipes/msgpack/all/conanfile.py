# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get, rmdir

required_conan_version = ">=1.52.0"


class MsgpackConan(ConanFile):
    name = "msgpack"
    description = "The official C++ library for MessagePack"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/msgpack/msgpack-c"
    topics = ("message-pack", "serialization")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "c_api": [True, False],
        "cpp_api": [True, False],
        "with_boost": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "c_api": True,
        "cpp_api": True,
        "with_boost": False,
        "header_only": False,
    }
    deprecated = "msgpack-c or msgpack-cxx"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        # Deprecate header_only option
        if self.options.header_only:
            self.options.c_api = False
            self.options.cpp_api = True
            self.output.warning("header_only option is deprecated, prefer c_api=False and cpp_api=True")
        self.options.rm_safe("header_only")

        if not self.options.c_api and not self.options.cpp_api:
            raise ConanInvalidConfiguration("You must enable at least c_api or cpp_api.")
        if self.options.c_api:
            if self.options.shared:
                self.options.rm_safe("fPIC")
            self.settings.rm_safe("compiler.libcxx")
            self.settings.rm_safe("compiler.cppstd")
        else:
            self.options.rm_safe("shared")
            self.options.rm_safe("fPIC")
        if not self.options.cpp_api:
            self.options.rm_safe("with_boost")
        if self.options.get_safe("with_boost"):
            self.options["boost"].header_only = False
            self.options["boost"].without_chrono = False
            self.options["boost"].without_context = False
            self.options["boost"].without_system = False
            self.options["boost"].without_timer = False

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("with_boost"):
            self.requires("boost/1.82.0")

    def package_id(self):
        del self.info.options.with_boost
        if not self.options.c_api:
            self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"
        tc.variables["MSGPACK_ENABLE_SHARED"] = self.options.shared
        tc.variables["MSGPACK_ENABLE_STATIC"] = not self.options.shared
        tc.variables["MSGPACK_ENABLE_CXX"] = self.options.cpp_api
        tc.variables["MSGPACK_BOOST"] = self.options.get_safe("with_boost", False)
        tc.variables["MSGPACK_32BIT"] = self.settings.arch == "x86"
        tc.variables["MSGPACK_BUILD_EXAMPLES"] = False
        tc.variables["MSGPACK_BUILD_TESTS"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        if self.options.get_safe("with_boost") and (
            self.dependencies["boost"].options.header_only
            or self.dependencies["boost"].options.without_chrono
            or self.dependencies["boost"].options.without_context
            or self.dependencies["boost"].options.without_system
            or self.dependencies["boost"].options.without_timer
        ):
            raise ConanInvalidConfiguration(
                "msgpack with boost requires the following boost components:"
                " chrono, context, system and timer."
            )
        if self.options.c_api:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(
            self, "LICENSE_1_0.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        if self.options.c_api:
            cmake = CMake(self)
            cmake.install()
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        else:
            copy(
                self,
                "*.h",
                dst=os.path.join(self.package_folder, "include"),
                src=os.path.join(self.source_folder, "include"),
            )
            copy(
                self,
                "*.hpp",
                dst=os.path.join(self.package_folder, "include"),
                src=os.path.join(self.source_folder, "include"),
            )

    def package_info(self):
        # TODO: CMake imported targets shouldn't be namespaced (waiting implementation of https://github.com/conan-io/conan/issues/7615)
        if self.options.c_api:
            self.cpp_info.components["msgpackc"].set_property("cmake_target_name", "msgpackc")
            self.cpp_info.components["msgpackc"].names["cmake_find_package"] = "msgpackc"
            self.cpp_info.components["msgpackc"].names["cmake_find_package_multi"] = "msgpackc"
            self.cpp_info.components["msgpackc"].libs = collect_libs(self)
        if self.options.cpp_api:
            self.cpp_info.components["msgpackc-cxx"].set_property("cmake_target_name", "msgpackc-cxx")
            self.cpp_info.components["msgpackc-cxx"].names["cmake_find_package"] = "msgpackc-cxx"
            self.cpp_info.components["msgpackc-cxx"].names["cmake_find_package_multi"] = "msgpackc-cxx"
            if self.options.with_boost:
                self.cpp_info.components["msgpackc-cxx"].defines = ["MSGPACK_USE_BOOST"]
                self.cpp_info.components["msgpackc-cxx"].requires = ["boost::boost"]
