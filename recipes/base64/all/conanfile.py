from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import copy, get, apply_conandata_patches, chdir, export_conandata_patches, rmdir
from conan.tools.env import Environment
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

import os

required_conan_version = ">=1.53.0"


class Base64Conan(ConanFile):
    name = "base64"
    description = "Fast Base64 stream encoder/decoder"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/aklomp/base64"
    topics = ("codec", "encoder", "decoder")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if Version(self.version) < "0.5.0":
            del self.options.shared
            self.package_type = "static-library"
        if self.options.get_safe("shared"):
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        if self._use_cmake:
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openmp:
            self.requires("llvm-openmp/18.1.8")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _use_cmake(self):
        return is_msvc(self) or Version(self.version) >= "0.5.0"

    def generate(self):
        if self._use_cmake:
            tc = CMakeToolchain(self)
            tc.variables["BASE64_BUILD_CLI"] = False
            tc.variables["BASE64_WERROR"] = False
            tc.variables["BASE64_BUILD_TESTS"] = False
            tc.variables["BASE64_WITH_OpenMP"] = self.options.with_openmp
            tc.generate()
            deps = CMakeDeps(self)
            deps.generate()
        else:
            tc = AutotoolsToolchain(self)
            tc.generate()
            deps = AutotoolsDeps(self)
            deps.generate()

    def build(self):
        apply_conandata_patches(self)
        if self._use_cmake:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            env = Environment()
            if self.settings.arch == "x86" or self.settings.arch == "x86_64":
                env.append("AVX2_CFLAGS", "-mavx2")
                env.append("SSSE3_CFLAGS", "-mssse3")
                env.append("SSE41_CFLAGS", "-msse4.1")
                env.append("SSE42_CFLAGS", "-msse4.2")
                env.append("AVX_CFLAGS", "-mavx")
            else:
                # ARM-specific instructions can be enabled here
                pass
            with env.vars(self).apply(), \
                 chdir(self, self.source_folder):
                autotools = Autotools(self)
                autotools.make(target="lib/libbase64.a")

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self._use_cmake:
            cmake = CMake(self)
            cmake.install()
            if Version(self.version) >= "0.5.0":
                rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
            else:
                rmdir(self, os.path.join(self.package_folder, "cmake"))
        else:
            copy(self, pattern="*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))
            copy(self, pattern="*.a", dst=os.path.join(self.package_folder, "lib"), src=self.source_folder, keep_path=False)
            copy(self, pattern="*.lib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "base64")
        self.cpp_info.set_property("cmake_target_name", "aklomp::base64")
        self.cpp_info.libs = ["base64"]

        if Version(self.version) >= "0.5.0" and not self.options.shared:
            self.cpp_info.defines.append("BASE64_STATIC_DEFINE")
