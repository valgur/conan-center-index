import os
import sys

from conan import ConanFile
# FIXME: linter complains, but function is there
# https://docs.conan.io/2.0/reference/tools/build.html?highlight=check_min_cppstd#conan-tools-build-check-max-cppstd
# from conan.tools.build import stdcpp_library, check_min_cppstd, check_max_cppstd
from conan.tools.build import stdcpp_library, check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import get, copy, rmdir, rm
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class vvencRecipe(ConanFile):
    name = "vvenc"
    description = "Fraunhofer Versatile Video Encoder (VVenC)"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.hhi.fraunhofer.de/en/departments/vca/technologies-and-solutions/h266-vvc.html"
    topics = ("video", "encoder", "codec", "vvc", "h266")
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

    def validate_build(self):
        # validates the minimum and maximum C++ standard supported
        # currently, the project can only be built with C++14 standard
        # it cannot be built with older standard because
        # it doesn't have all the C++ features needed
        # and it cannot be built with newer C++ standard
        # because they have existing C++ features removed
        check_min_cppstd(self, 14)
        if Version(self.version) < "1.10.0":
            # FIXME: linter complains, but function is there
            # https://docs.conan.io/2.0/reference/tools/build.html?highlight=check_min_cppstd#conan-tools-build-check-max-cppstd
            check_max_cppstd = getattr(sys.modules['conan.tools.build'], 'check_max_cppstd')
            check_max_cppstd(self, 14)

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe('fPIC')

    def layout(self):
        cmake_layout(self, src_folder='src')

    def package_id(self):
        # still important, older binutils cannot recognize
        # object files created with newer binutils,
        # thus linker cannot find any valid object and therefore symbols
        # (fails to find `vvenc_get_version`, which is obviously always there)
        # this is not exactly modeled by conan right now,
        # so "compiler" setting is closest thing to avoid an issue
        # (while technically it's not a compiler, but linker and archiver)
        # del self.info.settings.compiler
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["VVENC_ENABLE_LINK_TIME_OPT"] = False
        tc.cache_variables["VVENC_ENABLE_LINK_TIME_OPT"] = False
        tc.extra_cxxflags.append("-Wno-error=maybe-uninitialized")
        tc.extra_cxxflags.append("-Wno-error=uninitialized")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", 'pkgconfig'))
        rmdir(self, os.path.join(self.package_folder, 'lib', "cmake"))
        rm(self, "*.pdb", os.path.join(self.package_folder, 'bin'))
        rm(self, '*.pdb', os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["vvenc"]
        if self.options.shared:
            self.cpp_info.defines.extend(["VVENC_DYN_LINK"])  # vvcencDecl.h
        libcxx = stdcpp_library(self)  # source code is C++, but interface is pure C
        libcxx = [libcxx] if libcxx else []
        libm = ["m"] if self.settings.get_safe("os") == "Linux" else []
        libpthread = ['pthread'] if self.settings.get_safe('os') == 'Linux' else []
        self.cpp_info.system_libs.extend(libcxx + libm + libpthread)
