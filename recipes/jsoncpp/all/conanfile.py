from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file
from conan.tools.scm import Version
from conan.tools.microsoft import is_msvc
import os

required_conan_version = ">=2.1"


class JsoncppConan(ConanFile):
    name = "jsoncpp"
    description = "A C++ library for interacting with JSON."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/open-source-parsers/jsoncpp"
    topics = ("json", "parser", "config")
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
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["JSONCPP_WITH_TESTS"] = False
        tc.variables["JSONCPP_WITH_WARNING_AS_ERROR"] = False
        tc.variables["JSONCPP_WITH_CMAKE_PACKAGE"] = False
        tc.variables["JSONCPP_WITH_STRICT_ISO"] = False
        tc.variables["JSONCPP_WITH_PKGCONFIG_SUPPORT"] = False
        jsoncpp_version = Version(self.version)
        if jsoncpp_version < "1.9.0" or jsoncpp_version >= "1.9.4":
            tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        if jsoncpp_version >= "1.9.3":
            tc.variables["JSONCPP_WITH_EXAMPLE"] = False
        if jsoncpp_version >= "1.9.4":
            tc.variables["BUILD_OBJECT_LIBS"] = False
        if jsoncpp_version < "1.9.0":
            # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
            tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        # No opt-out of ccache
        if Version(self.version) < "1.9.3":
            tc.cache_variables["CCACHE_FOUND"] = ""
        else:
            tc.cache_variables["CCACHE_EXECUTABLE"] = ""
        tc.generate()

    def _patch_sources(self):
        if is_msvc(self) and str(self.settings.compiler.version) in ("11", "170"):
            replace_in_file(self, os.path.join(self.source_folder, "include", "json", "value.h"),
                                  "explicit operator bool()",
                                  "operator bool()")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "jsoncpp")
        self.cpp_info.set_property("cmake_target_name", "JsonCpp::JsonCpp")
        self.cpp_info.set_property(
            "cmake_target_aliases",
            ["jsoncpp_lib"] if self.options.shared else ["jsoncpp_lib", "jsoncpp_static", "jsoncpp_lib_static"],
        )
        self.cpp_info.set_property("pkg_config_name", "jsoncpp")
        self.cpp_info.libs = ["jsoncpp"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("JSON_DLL")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
