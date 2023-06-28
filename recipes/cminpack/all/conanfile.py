import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import rmdir, copy, get

required_conan_version = ">=1.53.0"


class CMinpackConan(ConanFile):
    name = "cminpack"
    description = (
        "About A C/C++ rewrite of the MINPACK software (originally in FORTRAN)"
        "for solving nonlinear equations and nonlinear least squares problems"
    )
    license = "LicenseRef-CopyrightMINPACK.txt"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://devernay.free.fr/hacks/cminpack/"
    topics = ("nonlinear", "solver")

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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

        # cminpack is a c library
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_EXAMPLES"] = "OFF"
        tc.variables["CMINPACK_LIB_INSTALL_DIR"] = "lib"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(
            self,
            "CopyrightMINPACK.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        rmdir(self, os.path.join(self.package_folder, "share"))  # contains cmake config files

    def _library_postfix(self):
        postfix = ""
        if not self.options.shared:
            postfix += "_s"  # for static
        if self.settings.build_type == "Debug":
            postfix += "_d"

        return postfix

    def package_info(self):
        minpack_include_dir = os.path.join("include", "cminpack-1")
        self.cpp_info.set_property("cmake_target_name", "cminpack")
        # the double precision version
        self.cpp_info.components["cminpack-double"].libs = ["cminpack" + self._library_postfix()]
        self.cpp_info.components["cminpack-double"].includedirs.append(minpack_include_dir)
        self.cpp_info.components["cminpack-double"].set_property("cmake_target_name", "cminpack::cminpack")
        self.cpp_info.components["cminpack-double"].set_property("pkg_config_name", "cminpack")
        self.cpp_info.components["cminpack-double"].names["cmake_find_package"] = "cminpack"
        self.cpp_info.components["cminpack-double"].names["cmake_find_package_multi"] = "cminpack"

        # the single precision version
        self.cpp_info.components["cminpack-single"].libs = ["cminpacks" + self._library_postfix()]
        self.cpp_info.components["cminpack-single"].includedirs.append(minpack_include_dir)
        self.cpp_info.components["cminpack-single"].defines.append("__cminpack_float__")
        self.cpp_info.components["cminpack-single"].set_property("cmake_target_name", "cminpack::cminpacks")
        self.cpp_info.components["cminpack-single"].set_property("pkg_config_name", "cminpacks")
        self.cpp_info.components["cminpack-single"].names["cmake_find_package"] = "cminpacks"
        self.cpp_info.components["cminpack-single"].names["cmake_find_package_multi"] = "cminpacks"

        if self.settings.os != "Windows":
            self.cpp_info.components["cminpack-double"].system_libs.append("m")
            self.cpp_info.components["cminpack-single"].system_libs.append("m")

        # required apple frameworks
        self.cpp_info.components["cminpack-double"].frameworks.append("Accelerate")
        self.cpp_info.components["cminpack-single"].frameworks.append("Accelerate")

        if not self.options.shared and self.settings.os == "Windows":
            self.cpp_info.components["cminpack-double"].defines.append("CMINPACK_NO_DLL")
            self.cpp_info.components["cminpack-single"].defines.append("CMINPACK_NO_DLL")
