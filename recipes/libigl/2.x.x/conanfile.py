# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class LibiglConan(ConanFile):
    name = "libigl"
    description = "Simple C++ geometry processing library"
    license = "MPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libigl.github.io/"
    topics = ("geometry", "matrices", "algorithms", "header-only")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "fPIC": True,
        "header_only": True,
    }
    no_copy_source = True

    @property
    def _minimum_cpp_standard(self):
        return 14

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16",
            "gcc": "6",
            "clang": "3.4",
            "apple-clang": "5.1",
        }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.header_only:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.3.9")

    def package_id(self):
        if self.options.header_only:
            self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warning(
                f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support."
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires C++{self._minimum_cpp_standard} support. The current compiler"
                    f" {self.settings.compiler} {self.settings.compiler.version} does not support it."
                )
        if is_msvc_static_runtime(self) and not self.options.header_only:
            raise ConanInvalidConfiguration("Visual Studio build with MT runtime is not supported")
        if "arm" in self.settings.arch or "x86" is self.settings.arch:
            raise ConanInvalidConfiguration(
                "Not available for arm. Requested arch: {}".format(self.settings.arch)
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIBIGL_EXPORT_TARGETS"] = True
        tc.variables["LIBIGL_USE_STATIC_LIBRARY"] = not self.options.header_only

        # All these dependencies are needed to build the examples or the tests
        tc.variables["LIBIGL_BUILD_TUTORIALS"] = "OFF"
        tc.variables["LIBIGL_BUILD_TESTS"] = "OFF"
        tc.variables["LIBIGL_BUILD_PYTHON"] = "OFF"

        tc.variables["LIBIGL_WITH_CGAL"] = False
        tc.variables["LIBIGL_WITH_COMISO"] = False
        tc.variables["LIBIGL_WITH_CORK"] = False
        tc.variables["LIBIGL_WITH_EMBREE"] = False
        tc.variables["LIBIGL_WITH_MATLAB"] = False
        tc.variables["LIBIGL_WITH_MOSEK"] = False
        tc.variables["LIBIGL_WITH_OPENGL"] = False
        tc.variables["LIBIGL_WITH_OPENGL_GLFW"] = False
        tc.variables["LIBIGL_WITH_OPENGL_GLFW_IMGUI"] = False
        tc.variables["LIBIGL_WITH_PNG"] = False
        tc.variables["LIBIGL_WITH_TETGEN"] = False
        tc.variables["LIBIGL_WITH_TRIANGLE"] = False
        tc.variables["LIBIGL_WITH_XML"] = False
        tc.variables["LIBIGL_WITH_PYTHON"] = "OFF"
        tc.variables["LIBIGL_WITH_PREDICATES"] = False
        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE.GPL", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "LICENSE.MPL2", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        rmdir(self, os.path.join(self.package_folder, "share"))
        if not self.options.header_only:
            rm(self, "*.c", self.package_folder, recursive=True)
            rm(self, "*.cpp", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libigl")
        self.cpp_info.set_property("cmake_target_name", "igl")

        self.cpp_info.components["igl_common"].set_property("cmake_target_name", "common")
        self.cpp_info.components["igl_common"].names["cmake_find_package"] = "common"
        self.cpp_info.components["igl_common"].names["cmake_find_package_multi"] = "common"
        self.cpp_info.components["igl_common"].libs = []
        self.cpp_info.components["igl_common"].requires = ["eigen::eigen"]
        if self.settings.os == "Linux":
            self.cpp_info.components["igl_common"].system_libs = ["pthread"]

        self.cpp_info.components["igl_core"].set_property("cmake_target_name", "core")
        self.cpp_info.components["igl_core"].names["cmake_find_package"] = "core"
        self.cpp_info.components["igl_core"].names["cmake_find_package_multi"] = "core"
        self.cpp_info.components["igl_core"].requires = ["igl_common"]
        if not self.options.header_only:
            self.cpp_info.components["igl_core"].libs = ["igl"]
            self.cpp_info.components["igl_core"].defines.append("IGL_STATIC_LIBRARY")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "libigl"
        self.cpp_info.filenames["cmake_find_package_multi"] = "libigl"
        self.cpp_info.names["cmake_find_package"] = "igl"
        self.cpp_info.names["cmake_find_package_multi"] = "igl"
