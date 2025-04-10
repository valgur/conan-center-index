import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class FlatccConan(ConanFile):
    name = "flatcc"
    description = "C language binding for Flatbuffers, an efficient cross platform serialization library"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dvidelabs/flatcc"
    topics = ("flatbuffers", "serialization")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "portable": [True, False],
        "gnu_posix_memalign": [True, False],
        "runtime_lib_only": [True, False],
        "verify_assert": [True, False],
        "verify_trace": [True, False],
        "reflection": [True, False],
        "native_optim": [True, False],
        "fast_double": [True, False],
        "ignore_const_condition": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "portable": False,
        "gnu_posix_memalign": True,
        "runtime_lib_only": False,
        "verify_assert": False,
        "verify_trace": False,
        "reflection": True,
        "native_optim": False,
        "fast_double": False,
        "ignore_const_condition": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os == "Windows":
            if is_msvc(self) and self.options.shared:
                # Building flatcc shared libs with Visual Studio is broken
                raise ConanInvalidConfiguration("Building flatcc libraries shared is not supported")
            if Version(self.version) == "0.6.0" and self.settings.compiler == "gcc":
                raise ConanInvalidConfiguration("Building flatcc with MinGW is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FLATCC_PORTABLE"] = self.options.portable
        tc.cache_variables["FLATCC_GNU_POSIX_MEMALIGN"] = self.options.gnu_posix_memalign
        tc.cache_variables["FLATCC_RTONLY"] = self.options.runtime_lib_only
        tc.cache_variables["FLATCC_INSTALL"] = True
        tc.cache_variables["FLATCC_COVERAGE"] = False
        tc.cache_variables["FLATCC_DEBUG_VERIFY"] = self.options.verify_assert
        tc.cache_variables["FLATCC_TRACE_VERIFY"] = self.options.verify_trace
        tc.cache_variables["FLATCC_REFLECTION"] = self.options.reflection
        tc.cache_variables["FLATCC_NATIVE_OPTIM"] = self.options.native_optim
        tc.cache_variables["FLATCC_FAST_DOUBLE"] = self.options.fast_double
        tc.cache_variables["FLATCC_IGNORE_CONST_COND"] = self.options.ignore_const_condition
        tc.cache_variables["FLATCC_TEST"] = False
        tc.cache_variables["FLATCC_ALLOW_WERROR"] = False
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        if self.settings.build_type == "Debug" and not self.settings.os == "Windows":
            debug_suffix = "_d" if self.settings.build_type == "Debug" else ""
            os.rename(os.path.join(self.package_folder, "bin", f"flatcc{debug_suffix}"),
                      os.path.join(self.package_folder, "bin", "flatcc"))
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        fix_apple_shared_install_name(self)

    def package_info(self):
        debug_suffix = "_d" if self.settings.build_type == "Debug" else ""
        if not self.options.runtime_lib_only:
            self.cpp_info.libs.append(f"flatcc{debug_suffix}")
        self.cpp_info.libs.append(f"flatccrt{debug_suffix}")
