# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class Pagmo2Conan(ConanFile):
    name = "pagmo2"
    description = "pagmo is a C++ scientific library for massively parallel optimization."
    license = ("LGPL-3.0-or-later", "GPL-3.0-or-later")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://esa.github.io/pagmo2"
    topics = ("pagmo", "optimization", "parallel-computing", "genetic-algorithm", "metaheuristics")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_eigen": [True, False],
        "with_nlopt": [True, False],
        "with_ipopt": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_eigen": False,
        "with_nlopt": False,
        "with_ipopt": False,
    }

    @property
    def _compilers_minimum_version(self):
        return {
            "Visual Studio": "15.7",
            "gcc": "7",
            "clang": "5.0",
            "apple-clang": "9.1",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.78.0")
        self.requires("onetbb/2020.3")
        if self.options.with_eigen:
            self.requires("eigen/3.4.0")
        if self.options.with_nlopt:
            self.requires("nlopt/2.7.1")

    @property
    def _required_boost_components(self):
        return ["serialization"]

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warning(
                f"{self.name} {self.version} requires C++17. "
                "Your compiler is unknown. Assuming it supports C++17."
            )
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.name} {self.version} requires C++17, which your compiler does not support."
            )

        # TODO: add ipopt support
        if self.options.with_ipopt:
            raise ConanInvalidConfiguration("ipopt recipe not available yet in CCI")

        miss_boost_required_comp = any(
            getattr(self.options["boost"], "without_{}".format(boost_comp), True)
            for boost_comp in self._required_boost_components
        )
        if self.options["boost"].header_only or miss_boost_required_comp:
            raise ConanInvalidConfiguration(
                "{0} requires non header-only boost with these components: {1}".format(
                    self.name, ", ".join(self._required_boost_components)
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PAGMO_BUILD_TESTS"] = False
        tc.variables["PAGMO_BUILD_BENCHMARKS"] = False
        tc.variables["PAGMO_BUILD_TUTORIALS"] = False
        tc.variables["PAGMO_WITH_EIGEN3"] = self.options.with_eigen
        tc.variables["PAGMO_WITH_NLOPT"] = self.options.with_nlopt
        tc.variables["PAGMO_WITH_IPOPT"] = self.options.with_ipopt
        tc.variables["PAGMO_ENABLE_IPO"] = False
        tc.variables["PAGMO_BUILD_STATIC_LIBRARY"] = not self.options.shared
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        # do not force MT runtime for static lib
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "if(YACMA_COMPILER_IS_MSVC AND PAGMO_BUILD_STATIC_LIBRARY)",
            "if(0)",
        )
        # No warnings as errors
        yacma_cmake = os.path.join(
            self.source_folder, "cmake_modules", "yacma", "YACMACompilerLinkerSettings.cmake"
        )
        replace_in_file(self, yacma_cmake, 'list(APPEND _YACMA_CXX_FLAGS_DEBUG "-Werror")', "")
        replace_in_file(self, yacma_cmake, "_YACMA_CHECK_ENABLE_DEBUG_CXX_FLAG(/W4)", "")
        replace_in_file(self, yacma_cmake, "_YACMA_CHECK_ENABLE_DEBUG_CXX_FLAG(/WX)", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="COPYING.*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "pagmo")
        self.cpp_info.set_property("cmake_target_name", "Pagmo::pagmo")
        # TODO: back to global scope in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.components["_pagmo"].libs = ["pagmo"]
        self.cpp_info.components["_pagmo"].requires = [
            "boost::headers",
            "boost::serialization",
            "onetbb::onetbb",
        ]
        if self.options.with_eigen:
            self.cpp_info.components["_pagmo"].requires.append("eigen::eigen")
        if self.options.with_nlopt:
            self.cpp_info.components["_pagmo"].requires.append("nlopt::nlopt")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_pagmo"].system_libs.append("pthread")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "pagmo"
        self.cpp_info.filenames["cmake_find_package_multi"] = "pagmo"
        self.cpp_info.names["cmake_find_package"] = "Pagmo"
        self.cpp_info.names["cmake_find_package_multi"] = "Pagmo"
        self.cpp_info.components["_pagmo"].names["cmake_find_package"] = "pagmo"
        self.cpp_info.components["_pagmo"].names["cmake_find_package_multi"] = "pagmo"
        self.cpp_info.components["_pagmo"].set_property("cmake_target_name", "Pagmo::pagmo")
